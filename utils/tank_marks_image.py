from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageDraw

_RENDER_SCALE = 4


def render_tank_marks_png(
    count: int,
    *,
    stripe_width: int,
    stripe_height: int,
    gap: int,
    overlap: int = 0,
    vertical_lift: int = 0,
    line_width_ratio: float = 0.32,
) -> bytes:
    if count <= 0:
        return b""

    step = max(1, stripe_width - overlap)
    output_width = stripe_width + max(0, count - 1) * (step + gap)
    output_height = stripe_height + max(0, vertical_lift)

    scale = _RENDER_SCALE
    stripe_w = max(1, stripe_width * scale)
    stripe_h = max(1, stripe_height * scale)
    stripe_step = max(1, step * scale)
    stripe_gap = max(0, gap * scale)
    pad_bottom = max(0, vertical_lift) * scale

    total_width = stripe_w + max(0, count - 1) * (stripe_step + stripe_gap)
    canvas_height = stripe_h + pad_bottom
    image = Image.new("RGBA", (total_width, canvas_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    color = (255, 209, 38, 255)
    line_width = max(1, int(stripe_w * line_width_ratio))

    inset = scale
    for index in range(count):
        left = index * (stripe_step + stripe_gap)
        right = left + stripe_w
        draw.line(
            [(left + inset, stripe_h - inset), (right - inset, inset)],
            fill=color,
            width=line_width,
        )

    output = image.resize(
        (output_width, output_height),
        Image.Resampling.LANCZOS,
    )

    buffer = BytesIO()
    output.save(buffer, format="PNG")
    return buffer.getvalue()
