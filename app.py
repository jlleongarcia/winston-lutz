import io
import tempfile
from datetime import datetime
from pathlib import Path

import pydicom
import streamlit as st
from pylinac import WinstonLutz

st.set_page_config(page_title="Winston-Lutz Analysis", layout="wide")
st.title("Winston-Lutz Analysis")


def extract_date_from_dicom(dicom_dir: Path) -> str | None:
    """Try to extract the study/acquisition date from the first DICOM file found."""
    for f in dicom_dir.iterdir():
        try:
            ds = pydicom.dcmread(f, stop_before_pixels=True)
            for tag in ("AcquisitionDate", "StudyDate", "ContentDate"):
                raw = getattr(ds, tag, None)
                if raw:
                    return datetime.strptime(str(raw), "%Y%m%d").strftime("%d-%m-%Y")
        except Exception:
            continue
    return None


# ── Sidebar parameters ───────────────────────────────────────────────
st.sidebar.header("Analysis parameters")
bb_size = st.sidebar.number_input("BB size (mm)", min_value=1.0, max_value=20.0, value=8.0, step=0.5)

# ── File upload ──────────────────────────────────────────────────────
uploaded_files = st.file_uploader(
    "Upload Winston-Lutz DICOM images",
    type=["dcm", "DCM"],
    accept_multiple_files=True,
)

if not uploaded_files:
    st.info("Upload at least 2 DICOM images to begin the analysis.")
    st.stop()

if len(uploaded_files) < 2:
    st.warning("At least 2 images are required for Winston-Lutz analysis.")
    st.stop()

# ── Save uploads to a temp directory ─────────────────────────────────
tmp_dir = tempfile.mkdtemp()
tmp_path = Path(tmp_dir)
for uf in uploaded_files:
    (tmp_path / uf.name).write_bytes(uf.getvalue())

# ── Try to extract date from the DICOM metadata ─────────────────────
dicom_date = extract_date_from_dicom(tmp_path)
analysis_date = dicom_date or datetime.now().strftime("%d-%m-%Y")

st.sidebar.markdown(f"**Analysis date:** {analysis_date}")

# ── Run analysis ─────────────────────────────────────────────────────
with st.spinner("Running Winston-Lutz analysis…"):
    try:
        wl = WinstonLutz(str(tmp_path))
        wl.analyze(bb_size_mm=bb_size)
    except Exception as e:
        st.error(f"Analysis failed: {e}")
        st.stop()

# ── Results ──────────────────────────────────────────────────────────
st.header("Results")
st.text(wl.results())

# ── Plotly interactive figures ───────────────────────────────────────
st.header("Analyzed images")
try:
    figs = wl.plotly_analyzed_images(show=False)
    for name, fig in figs.items():
        st.subheader(name)
        st.plotly_chart(fig, use_container_width=True)
except Exception:
    # Fallback to matplotlib if plotly method unavailable
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figs_mpl, names = wl.plot_images(show=False)
    for fig, name in zip(figs_mpl, names):
        st.subheader(name)
        st.pyplot(fig)
        plt.close(fig)

    st.subheader("Summary")
    wl.plot_summary(show=False)
    st.pyplot(plt.gcf())
    plt.close("all")

# ── PDF report download ─────────────────────────────────────────────
st.header("PDF Report")
pdf_buffer = io.BytesIO()
wl.publish_pdf(
    pdf_buffer,
    notes=[f"Analysis date: {analysis_date}"],
    metadata={"Date": analysis_date},
)
pdf_buffer.seek(0)

pdf_filename = f"Winston-Lutz_{analysis_date}.pdf"
st.download_button(
    label="Download PDF report",
    data=pdf_buffer,
    file_name=pdf_filename,
    mime="application/pdf",
)
