from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.templating import Jinja2Templates

import os
import numpy as np
import logging


# 1) Import your TradingView screener classes
#    (Adjust as needed for your actual code/installation path.)
from tradingview_screener import Query, Column


#model = YOLO('screener/models/best.pt')
#templates = Jinja2Templates(directory="templates")

# 2) Define your rating formatter
def format_technical_rating(rating: float) -> str:
    """Convert numeric rating to a descriptive string."""
    if rating >= 0.5:
        return 'Strong Buy'
    elif rating >= 0.1:
        return 'Buy'
    elif rating >= -0.1:
        return 'Neutral'
    elif rating >= -0.5:
        return 'Sell'
    else:
        return 'Strong Sell'

# 3) Placeholder YOLO model class
#    Replace with your actual YOLO model code/initialization logic.


# Instantiate FastAPI
app = FastAPI()

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Logger (optional)
logger = logging.getLogger("my_fastapi_app")
logger.setLevel(logging.INFO)


@app.get("/tradingview_data", response_class=HTMLResponse)
def show_tradingview_data(request: Request):
    """
    Retrieve and display trading data in an HTML table using a template.
    """
    try:
        # Query the data from tradingview_screener
        # The .get_scanner_data() often returns either a DataFrame directly
        # or a (metadata, DataFrame) tuple, depending on the library version.
        data_tuple = (
            Query()
            .select(
                'name',
                'Recommend.All',
                'close',
                'change_from_open',
                'volume',
                'RSI',
                'EMA5',
                'EMA10',
                'High.1M',
                'average_volume_10d_calc'
            )
            .set_markets('america')
            .where(
                Column('High.1M') == Column('close'),
                # Column('EMA5').crosses_above(Column('EMA10')),
                Column('RSI') > 30,
                Column('exchange').isin(['NASDAQ', 'NYSE', 'AMEX', 'NYSE ARCA']),
                Column('close') > 1.5,
                Column('volume') > Column('average_volume_10d_calc')
            )
            .order_by('name', ascending=False)
            .get_scanner_data()
        )

        # You may need to adapt this if the library returns only a DataFrame or a different structure
        if isinstance(data_tuple, tuple) and len(data_tuple) == 2:
            _, df = data_tuple  # e.g., (metadata, df)
        else:
            # If the library just returns a DataFrame, do:
            # df = data_tuple
            # Or handle as needed
            df = data_tuple

        # Convert DataFrame to a list of dict rows
        data_records = df.to_dict(orient='records')

        # Format the 'Recommend.All' column using our rating function
        for row in data_records:
            # Make sure 'Recommend.All' is numeric or castable to float
            try:
                rating_value = float(row.get('Recommend.All', 0))
            except:
                rating_value = 0
            row['Recommend.All'] = format_technical_rating(rating_value)

        # Render the template with the data
        return templates.TemplateResponse(
            "tradingview_data.html",
            {
                "request": request,
                "data": data_records
            }
        )
    except Exception as e:
        logger.error(f"Error retrieving trading data: {e}", exc_info=True)
        # Return a simple error page or JSON error
        return HTMLResponse(
            content=f"<h1>Error</h1><p>{str(e)}</p>", status_code=500
        )
