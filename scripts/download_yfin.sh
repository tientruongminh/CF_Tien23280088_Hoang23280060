%%bash
python src/yfin_downloader.py \
    --input american_companies/nasdaq-listed.csv \
    --outdir data/yfinance \
    --threads 8 \
    --adjust