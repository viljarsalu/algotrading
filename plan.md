# Plan: Configure dYdX V4 API Credentials

This plan outlines the steps to correctly configure the new dYdX V4 API credentials and deprecate the legacy V3 keys.

## 1. Define V4 Configuration Model
- **Goal:** Create a Pydantic settings model to load and validate the new V4 API keys from the `.env` file.
- **File:** `dydx-trading-service/backend/src/core/config.py`
- **Action:** Add a `DydxV4Settings` class to manage `apiwalletaddress` and `privatekey`.

## 2. Integrate V4 Settings into Application
- **Goal:** Make the new V4 settings accessible to the rest of the application.
- **File:** `dydx-trading-service/backend/src/core/config.py`
- **Action:** Add the `DydxV4Settings` to the main `ApplicationSettings` class.

## 3. Update dYdX Client Initialization
- **Goal:** Use the new configuration to initialize the dYdX client.
- **File:** `dydx-trading-service/backend/src/bot/dydx_client.py`
- **Action:** Modify the `create_client` method to read the `privatekey` and `walletaddress` from the settings instead of accepting them as parameters.

## 4. Activate V4 Credentials in `.env`
- **Goal:** Update the `.env` file to use the new V4 credentials.
- **File:** `dydx-trading-service/.env`
- **Action:**
    - Rename `apiwalletaddress` to `DYDX_V4_API_WALLET_ADDRESS`.
    - Rename `privatekey` to `DYDX_V4_PRIVATE_KEY`.
    - Uncomment these lines so the application can load them.
    - Confirm the legacy V3 keys (`DYDX_API_KEY`, etc.) remain empty as they are deprecated.

This approach ensures a clean, secure, and maintainable integration of your new dYdX V4 credentials.