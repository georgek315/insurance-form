import asyncio
import os
import gspread

from google.oauth2.service_account import Credentials
from playwright.async_api import async_playwright


SERVICE_ACCOUNT_FILE = "service_account.json"

SHEET_NAME = "Insurance_Data"

SESSION_FILE = "session.json"


FACTORIES = [
    "ABARTH",
    "ALFA ROMEO",
    "AUDI",
    "BMW",
    "FIAT",
    "FORD",
    "SEAT",
    "TOYOTA",
    "VOLKSWAGEN"
]


def get_models_sheet():

    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )

    client = gspread.authorize(creds)

    spreadsheet = client.open(SHEET_NAME)

    try:
        sheet = spreadsheet.worksheet("Models")

    except:

        sheet = spreadsheet.add_worksheet(
            title="Models",
            rows=5000,
            cols=5
        )

        sheet.append_row(
            [
                "factory",
                "model",
                "version",
                "engine",
                "power"
            ]
        )

    return sheet



async def main():


    sheet = get_models_sheet()


    existing = sheet.get_all_values()

    existing_keys = set()

    for row in existing[1:]:

        if len(row) >= 2:

            existing_keys.add(
                row[0]+"|"+row[1]
            )


    async with async_playwright() as p:


        browser = await p.chromium.launch(
            headless=True
        )


        context = await browser.new_context(
            storage_state=SESSION_FILE
        )


        page = await context.new_page()



        await page.goto(
            "https://www.webinsurer.gr/moneto/quoting/index",
            wait_until="networkidle"
        )


        for factory in FACTORIES:


            print(
                "Λήψη:",
                factory
            )


            response = await page.request.post(

                "https://www.webinsurer.gr/moneto/quoting/get-models",

                form={

                    "Q_FACTORY": factory,

                    "Q_MODEL": "",

                    "Q_DURATION": "6",

                    "Q_USAGE": "00",

                    "Q_ENTITY_TYPE": "1",

                    "act": "insert"

                }

            )


            data = await response.json()



            for item in data:


                key = (
                    factory
                    +
                    "|"
                    +
                    item["model"]
                )


                if key not in existing_keys:


                    sheet.append_row(

                        [

                            factory,

                            item.get("model",""),

                            item.get("version",""),

                            item.get("engine",""),

                            item.get("power","")

                        ]

                    )


                    existing_keys.add(key)



        await browser.close()



if __name__ == "__main__":

    asyncio.run(main())
