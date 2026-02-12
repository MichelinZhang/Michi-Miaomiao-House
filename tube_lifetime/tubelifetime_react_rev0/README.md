# Tube Lifetime Tester

This project is a web-based application for controlling and monitoring a tube lifetime tester. It consists of a React frontend and a FastAPI backend.

## Architecture

### System Layers

*   **Frontend**: The frontend is a single-page application built with React and Vite. It uses Tailwind CSS for styling and Framer Motion for animations. It's responsible for:
    *   Displaying the user interface.
    *   Sending control commands to the backend (start, pause, stop).
    *   Displaying real-time status and telemetry data from the backend.
*   **Backend**: The backend is a Python application built with FastAPI. It's responsible for:
    *   Providing a REST API for controlling the test engine.
    *   Providing a WebSocket endpoint for streaming real-time data to the frontend.
    *   Orchestrating the test engine and hardware drivers.
*   **Engine/Driver**: This layer is responsible for the core test logic and communication with the hardware.
    *   `engine.py`: Contains the `TestEngine` class, which manages the test sequence, state (running, paused), and threads.
    *   `driver.py`: Contains the `CylinderDriver` class, which handles the low-level communication with the hardware (or simulates it).

### Runtime Data Flow

*   **Control Flow**:
    1.  The user interacts with the UI in the frontend.
    2.  The frontend sends an HTTP request to the backend's REST API (e.g., `/api/start`).
    3.  The backend's API handler calls the appropriate method on the `TestEngine`.
*   **Status Flow**:
    1.  The `TestEngine` runs the test sequence in a separate thread.
    2.  The `TestEngine` and `CylinderDriver` send status updates, telemetry data, and logs to the frontend via WebSocket messages.
    3.  The frontend receives the WebSocket messages and updates the UI accordingly.

### Key Module Responsibilities

*   **`main.py`**:
    *   Sets up the FastAPI application and middleware.
    *   Defines the REST API endpoints (`/api/start`, `/api/pause`, `/api/stop`).
    *   Defines the WebSocket endpoint (`/ws`).
    *   Initializes the `TestEngine`.
*   **`engine.py`**:
    *   Manages the test state (running, paused, etc.).
    *   Executes the test sequence in a background thread.
    *   Communicates with the `CylinderDriver` to control the hardware.
    *   Sends updates to the frontend via the `broadcast_func`.
*   **`driver.py`**:
    *   Provides a high-level interface for controlling the cylinders.
    *   Handles the low-level communication with the hardware via `minimalmodbus`.
    *   Includes a simulation mode for development without hardware.

### Local Development

*   **Ports**:
    *   Frontend (Vite): `5173`
    *   Backend (FastAPI): `8000`
*   **Startup**:
    1.  Start the backend by running `python backend/main.py`.
    2.  Start the frontend by running `npm run dev` in the `frontend` directory.
    3.  The `start_project.bat` script can be used to start both the frontend and backend simultaneously.

## How to Run

1.  **Install Dependencies**:
    *   Backend: `pip install -r backend/requirements.txt`
    *   Frontend: `npm install` in the `frontend` directory.
2.  **Run the application**:
    *   Use the `start_project.bat` script to start both the backend and frontend.
    *   Alternatively, start the backend and frontend separately as described in the "Local Development" section.
3.  **Access the application**:
    *   Open your browser and navigate to `http://localhost:5173`.