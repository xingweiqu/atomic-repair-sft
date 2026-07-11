"""Frozen figure style (figs/FIGURE_STYLE.md is the spec; this is the only rc entry)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: F401

OKABE = dict(A1="#0072B2", B="#009E73", C="#E69F00", D="#CC79A7",
             placebo="#999999", drills="#D55E00", format_="#56B4E9",
             conduct="#F0E442", scaffold="#009E73", phrasing="#CC79A7",
             rule="#E69F00", black="#000000")
matplotlib.rcParams.update({
    "font.family": "sans-serif", "font.size": 9,
    "axes.titlesize": 10, "xtick.labelsize": 8, "ytick.labelsize": 8,
    "lines.linewidth": 1.5, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "axes.grid.axis": "y", "grid.alpha": 0.25,
    "figure.dpi": 120, "savefig.bbox": "tight", "pdf.fonttype": 42,
})


def save(fig, name, caption, sources, claims):
    """PDF+PNG dual output + three-piece meta file."""
    from pathlib import Path
    out = Path(__file__).parent / "out"
    out.mkdir(exist_ok=True)
    fig.savefig(out / f"{name}.pdf")
    fig.savefig(out / f"{name}.png", dpi=300)
    (out / f"{name}.meta.md").write_text(
        f"# {name}\n\n**Caption draft**: {caption}\n\n"
        f"**Data sources**:\n" + "".join(f"- {s}\n" for s in sources)
        + f"\n**Supports CLAIMS**: {claims}\n")
    print(f"saved {name}")
