"""Runtime controls for LoRA enablement, scaling, and adapter selection."""

import math
from typing import Any

from loguru import logger

from acestep.constants import DEBUG_MODEL_LOADING
from acestep.debug_utils import debug_log


def _toggle_lokr(decoder, enable: bool, scale: float = 1.0) -> bool:
    """Toggle a LyCORIS LoKr adapter via its multiplier.

    Args:
        decoder: Model decoder that may carry a ``_lycoris_net`` attribute.
        enable: ``True`` to activate (restore multiplier), ``False`` to zero it.
        scale: Multiplier value when enabling (default 1.0).

    Returns:
        ``True`` if a LyCORIS net was found and toggled, ``False`` otherwise.
    """
    lycoris_net = getattr(decoder, "_lycoris_net", None)
    if lycoris_net is None:
        return False
    set_mul = getattr(lycoris_net, "set_multiplier", None)
    if not callable(set_mul):
        return False
    target = float(scale) if enable else 0.0
    set_mul(target)
    logger.info(f"LoKr multiplier set to {target}")
    return True


def set_use_lora(self, use_lora: bool) -> str:
    """Toggle LoRA/LoKr usage for inference."""
    if use_lora and not self.lora_loaded:
        return "❌ No LoRA adapter loaded. Please load a LoRA first."

    self.use_lora = use_lora
    model = getattr(self, "model", None)
    decoder = getattr(model, "decoder", None) if model is not None else None
    if self.lora_loaded and decoder is None:
        logger.warning(
            "LoRA is marked as loaded, but model/decoder is unavailable during toggle."
        )

    if self.lora_loaded and decoder is not None:
        adapter_type = getattr(self, "_adapter_type", None)

        # LoKr (LyCORIS) path: toggle via set_multiplier
        if adapter_type == "lokr":
            active = getattr(self, "_lora_active_adapter", None)
            scale = (
                getattr(self, "_active_loras", {}).get(active, 1.0)
                if active
                else self.lora_scale
            )
            toggled = _toggle_lokr(decoder, use_lora, scale=scale)
            if not toggled:
                logger.warning(
                    "LoKr adapter type set but no _lycoris_net found on decoder"
                )

        # PEFT LoRA path: toggle via enable/disable adapter layers
        elif hasattr(decoder, "disable_adapter_layers"):
            try:
                if use_lora:
                    active = getattr(self, "_lora_active_adapter", None)
                    if active and hasattr(decoder, "set_adapter"):
                        try:
                            decoder.set_adapter(active)
                        except Exception:
                            pass
                    decoder.enable_adapter_layers()
                    logger.info("LoRA adapter enabled")
                    scale = getattr(self, "_active_loras", {}).get(active, 1.0)
                    if active and scale != 1.0:
                        self.set_lora_scale(active, scale)
                else:
                    decoder.disable_adapter_layers()
                    logger.info("LoRA adapter disabled")
            except Exception as e:
                logger.warning(f"Could not toggle adapter layers: {e}")

    adapter_label = "LoKr" if getattr(self, "_adapter_type", None) == "lokr" else "LoRA"
    status = "enabled" if use_lora else "disabled"
    return f"✅ {adapter_label} {status}"


def set_lora_scale(
    self, adapter_name_or_scale: str | float, scale: float | None = None
) -> str:
    """Set LoRA scale (0–1). Call as set_lora_scale(scale) or set_lora_scale(adapter_name, scale)."""
    if not self.lora_loaded:
        return "⚠️ No LoRA loaded"

    if scale is None:
        # Single-arg: first arg is scale, use active adapter
        scale_value = adapter_name_or_scale
        effective_name = None
    else:
        effective_name = (
            adapter_name_or_scale if isinstance(adapter_name_or_scale, str) else None
        )
        scale_value = scale

    try:
        scale_value = float(scale_value)
    except (TypeError, ValueError):
        return "❌ Invalid LoRA scale: please provide a numeric value between 0 and 1."
    if not math.isfinite(scale_value):
        return "❌ Invalid LoRA scale: please provide a finite numeric value between 0 and 1."

    scale_value = max(0.0, min(1.0, scale_value))
    _active_loras = getattr(self, "_active_loras", None) or {}
    if not effective_name:
        effective_name = getattr(self, "_lora_active_adapter", None) or (
            next(iter(_active_loras), None) if _active_loras else None
        )
    if not effective_name:
        return "❌ No adapter specified and no active adapter. Load a LoRA or pass adapter_name."

    self._active_loras[effective_name] = scale_value
    self.lora_scale = (
        scale_value  # backward compat: single "current" scale for status/UI
    )

    adapter_label = "LoKr" if getattr(self, "_adapter_type", None) == "lokr" else "LoRA"

    if not self.use_lora:
        logger.info(
            f"{adapter_label} scale for '{effective_name}' set to {scale_value:.2f} (will apply when enabled)"
        )
        return f"✅ {adapter_label} scale ({effective_name}): {scale_value:.2f} ({adapter_label} disabled)"

    # LoKr (LyCORIS) path: apply scale via set_multiplier
    if getattr(self, "_adapter_type", None) == "lokr":
        decoder = getattr(getattr(self, "model", None), "decoder", None)
        if decoder is not None:
            toggled = _toggle_lokr(decoder, True, scale=scale_value)
            if toggled:
                return f"✅ {adapter_label} scale ({effective_name}): {scale_value:.2f}"
            logger.warning("LoKr adapter type set but no _lycoris_net found for scale")
        return (
            f"⚠️ {adapter_label} scale set to {scale_value:.2f} (no LyCORIS net found)"
        )

    # PEFT LoRA path: apply scale via registry
    try:
        rebuilt_adapters: list[str] | None = None
        if not getattr(self, "_lora_adapter_registry", None):
            _, rebuilt_adapters = self._rebuild_lora_registry()

        if rebuilt_adapters is not None:
            if effective_name not in (rebuilt_adapters or []):
                return f"❌ Adapter '{effective_name}' not in loaded adapters: {rebuilt_adapters}"
            active_adapter = self._lora_service.active_adapter or effective_name
            if active_adapter != effective_name:
                self._lora_service.set_active_adapter(effective_name)
                self._lora_active_adapter = effective_name
                if getattr(self.model, "decoder", None) and hasattr(
                    self.model.decoder, "set_adapter"
                ):
                    try:
                        self.model.decoder.set_adapter(effective_name)
                    except Exception:
                        pass
        else:
            active_adapter = self._lora_service.ensure_active_adapter()
            self._lora_active_adapter = active_adapter
        self._sync_lora_state_from_service()
        adapter_names = list(self._lora_service.registry.keys())

        debug_log(
            lambda: (
                f"LoRA scale request: adapter={effective_name} scale={scale_value:.3f} "
                f"adapters={adapter_names}"
            ),
            mode=DEBUG_MODEL_LOADING,
            prefix="lora",
        )

        modified = self._apply_scale_to_adapter(effective_name, scale_value)
        report = getattr(self, "_lora_last_scale_report", {})
        skipped_total = sum(report.get("skipped_by_kind", {}).values())

        if modified > 0:
            logger.info(
                f"LoRA scale for '{effective_name}' set to {scale_value:.2f} "
                f"(modified={modified}, by_kind={report.get('modified_by_kind', {})}, skipped={report.get('skipped_by_kind', {})})"
            )
            return (
                f"✅ LoRA scale ({effective_name}): {scale_value:.2f}"
                if skipped_total == 0
                else f"✅ LoRA scale ({effective_name}): {scale_value:.2f} (skipped {skipped_total} targets)"
            )

        if skipped_total > 0:
            logger.warning(
                f"No LoRA targets were modified for adapter '{effective_name}' "
                f"(skipped={report.get('skipped_by_kind', {})})"
            )
            return f"⚠️ LoRA scale unchanged: {scale_value:.2f} (skipped {skipped_total} targets)"

        logger.warning(
            f"No registered LoRA scaling targets found for adapter '{effective_name}'"
        )
        return f"⚠️ Scale set to {scale_value:.2f} (no modules found)"
    except Exception as e:
        logger.warning(f"Could not set LoRA scale: {e}")
        return f"⚠️ Scale set to {scale_value:.2f} (partial)"


def set_active_lora_adapter(self, adapter_name: str) -> str:
    """Set the active LoRA adapter for scaling/inference.

    Two state holders can carry adapter records: ``_lora_service.registry``
    (populated from PEFT adapters discovered on the decoder) and
    ``_active_loras`` (the bookkeeping dict mirrored in the UI dataframe).
    LoKr / LyCORIS adapters never land in the PEFT registry, and some
    PEFT edge cases leave it empty too, so we accept any adapter name
    that lives in ``_active_loras`` as a fallback and apply the right
    side-effect for its adapter type.
    """
    self._ensure_lora_registry()

    # Preferred path: PEFT registry has the adapter → delegate to the
    # service which updates its internal active-adapter pointer too.
    if self._lora_service.set_active_adapter(adapter_name):
        self._lora_active_adapter = self._lora_service.active_adapter
        debug_log(
            f"Selected active LoRA adapter: {adapter_name}",
            mode=DEBUG_MODEL_LOADING,
            prefix="lora",
        )
        decoder = (
            getattr(self.model, "decoder", None) if self.model is not None else None
        )
        if decoder is not None and hasattr(decoder, "set_adapter"):
            try:
                decoder.set_adapter(adapter_name)
            except Exception:
                pass
        return f"✅ Active LoRA adapter: {adapter_name}"

    # Fallback: adapter is tracked in _active_loras but the PEFT
    # registry never saw it (LoKr, or a PEFT introspection miss).
    _active_loras = getattr(self, "_active_loras", None) or {}
    if adapter_name not in _active_loras:
        return f"❌ Unknown adapter: {adapter_name}"

    self._lora_active_adapter = adapter_name
    debug_log(
        f"Selected active LoRA adapter (via _active_loras fallback): {adapter_name}",
        mode=DEBUG_MODEL_LOADING,
        prefix="lora",
    )

    decoder = getattr(self.model, "decoder", None) if self.model is not None else None

    # PEFT path: the decoder may still know the adapter even though the
    # registry didn't expose it (e.g. stacked under LyCORIS). Try the
    # call defensively.
    if decoder is not None and hasattr(decoder, "set_adapter"):
        try:
            decoder.set_adapter(adapter_name)
        except Exception:
            pass

    # LoKr path: re-apply the stored scale through set_multiplier so the
    # newly-active adapter's intensity matches what the user sees in the
    # dataframe.
    if getattr(self, "_adapter_type", None) == "lokr" and decoder is not None:
        scale = _active_loras.get(adapter_name, 1.0)
        if self.use_lora:
            _toggle_lokr(decoder, True, scale=scale)

    return f"✅ Active LoRA adapter: {adapter_name}"


def clear_active_lora_adapter(self) -> str:
    """Remove the currently-active adapter pointer without unloading anything.

    Paired with ``set_active_lora_adapter``: the adapters stay loaded and
    visible in the multi-LoRA dataframe, but no row carries the active
    marker anymore. For LoKr we zero the LyCORIS multiplier; for PEFT we
    disable the adapter layers via ``disable_adapter_layers`` when the
    decoder exposes it.

    Returns:
        A human-readable status message describing the new state.
    """
    # Capture the caller's view of "what was active" BEFORE calling
    # ensure_lora_registry — that helper re-syncs _lora_active_adapter
    # from _lora_service.active_adapter, which is usually None in the
    # LoKr path and would clobber our read here.
    previous = getattr(self, "_lora_active_adapter", None)

    self._ensure_lora_registry()

    if previous is None:
        previous = getattr(self, "_lora_active_adapter", None)
    if previous is None:
        return "ℹ️ No adapter was active."

    self._lora_active_adapter = None
    # Best-effort: mirror the state on the backing lora_service so other
    # code paths agree on "no active adapter".
    try:
        self._lora_service.active_adapter = None
    except Exception:
        pass

    debug_log(
        f"Cleared active LoRA adapter (was '{previous}')",
        mode=DEBUG_MODEL_LOADING,
        prefix="lora",
    )

    decoder = getattr(self.model, "decoder", None) if self.model is not None else None
    adapter_type = getattr(self, "_adapter_type", None)

    if decoder is None:
        return f"✅ Adapter '{previous}' deactivated (no decoder loaded)."

    if adapter_type == "lokr":
        _toggle_lokr(decoder, False)
        return f"✅ LoKr adapter '{previous}' deactivated."

    # PEFT path: disable the adapter layers so inference runs with the
    # base decoder until the user re-activates another row.
    if hasattr(decoder, "disable_adapter_layers"):
        try:
            decoder.disable_adapter_layers()
        except Exception as exc:  # noqa: BLE001 - best effort
            logger.warning(f"Could not disable adapter layers: {exc}")

    return f"✅ LoRA adapter '{previous}' deactivated."


def get_lora_status(self) -> dict[str, Any]:
    """Get current LoRA status."""
    self._ensure_lora_registry()
    _active_loras = getattr(self, "_active_loras", None) or {}
    return {
        "loaded": self.lora_loaded,
        "active": self.use_lora,
        "scale": self.lora_scale,
        "scales": dict(_active_loras),
        "active_adapter": self._lora_active_adapter,
        "adapters": list(self._lora_service.registry.keys()),
        "synthetic_default_mode": self._lora_service.synthetic_default_mode,
        # Per-handler adapter type — either "lora" (PEFT) or "lokr"
        # (LyCORIS). The backend constraint of one-type-at-a-time means
        # every row in ``scales`` shares this type, so the UI can surface
        # a single badge per row without tracking it per-adapter.
        "adapter_type": getattr(self, "_adapter_type", None),
    }
