# Drug Traceability in Healthcare Supply Chain using Blockchain Technology

A blockchain-based solution for tracking and tracing pharmaceutical products throughout the healthcare supply chain, ensuring authenticity and preventing counterfeiting.

## Features

- **Smart Contract Integration**: Ethereum-based smart contract for immutable drug tracking
- **User Roles**: 
  - Admin: Manages users and oversees the system
  - Manufacturer: Adds new drugs to the blockchain
  - Distributor: Updates drug location and status
  - Retailer: Final point of sale tracking
  - Consumer: Verifies drug authenticity
- **Drug Tracing**: Complete history of each drug from manufacturing to consumption
- **Authentication**: Secure login system for all stakeholders
- **Real-time Updates**: Instant blockchain updates for drug status changes

## Demo Screenshots:
<img width="1899" height="962" alt="Screenshot 2025-07-12 165014" src="https://github.com/user-attachments/assets/814daeee-4be6-4e59-9180-1867d84ade2a" />
<img width="1916" height="890" alt="Screenshot 2025-07-12 165036" src="https://github.com/user-attachments/assets/d8af9e3c-3c46-4300-a34e-6d810e0c0089" />
<img width="1882" height="880" alt="Screenshot 2025-07-12 165150" src="https://github.com/user-attachments/assets/0f605acb-d13b-4ff8-ae4c-5f8680ca5758" />
<img width="1906" height="882" alt="Screenshot 2025-07-12 165220" src="https://github.com/user-attachments/assets/900f5010-9cd9-4354-b371-46a96ac99527" />

## Technology Stack

- **Backend**: Django (Python)
- **Frontend**: HTML, CSS, JavaScript
- **Blockchain**: Ethereum Smart Contracts (Solidity)
- **Database**: SQLite (Development), PostgreSQL (Production)
- **Web3 Integration**: Web3.py

## Prerequisites

- Python 3.8+
- Node.js and npm (for web3 dependencies)
- MetaMask or similar Web3 wallet
- Ethereum network access (Testnet/Mainnet)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/varshitha127/drug_traceability.git
   cd drug_traceability
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the root directory with:
   ```
   SECRET_KEY=your_django_secret_key
   DEBUG=True
   WEB3_PROVIDER_URI=your_ethereum_node_url
   ```

5. Run migrations:
   ```bash
   python manage.py migrate
   ```

6. Start the development server:
   ```bash
   python manage.py runserver
   ```

## Smart Contract Deployment

1. Deploy the smart contract (`Drug.sol`) to your chosen Ethereum network
2. Update the contract address in `DrugTraceApp/services/blockchain.py`
3. Ensure your Web3 provider is properly configured

## Usage

1. Access the application at `http://localhost:8000`
2. Connect your Web3 wallet (MetaMask)
3. Login with appropriate credentials
4. Follow the role-specific workflows for drug tracing

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

Varshitha - [@varshitha127](https://github.com/varshitha127)

Project Link: [https://github.com/varshitha127/drug_traceability](https://github.com/varshitha127/drug_traceability)

## Project Structure

```
drug_traceability/
│
├── DrugTraceApp/                  # Main Django application
│   ├── services/                  # Blockchain and business logic services
│   ├── templates/                 # HTML templates
│   │   ├── admin/                # Admin interface templates
│   │   ├── auth/                 # Authentication templates
│   │   ├── manufacturer/         # Manufacturer role templates
│   │   ├── distributor/          # Distributor role templates
│   │   ├── retailer/            # Retailer role templates
│   │   └── consumer/            # Consumer role templates
│   │
│   ├── static/                   # Static files (CSS, JS, Images)
│   │   ├── css/                 # Stylesheets
│   │   ├── js/                  # JavaScript files
│   │   └── images/              # Image assets
│   │
│   ├── migrations/              # Database migrations
│   ├── __init__.py
│   ├── admin.py                 # Admin site configuration
│   ├── apps.py                  # App configuration
│   ├── forms.py                 # Form definitions
│   ├── models.py                # Database models
│   ├── settings.py              # Development settings
│   ├── settings_prod.py         # Production settings
│   ├── urls.py                  # URL routing
│   ├── views.py                 # View functions
│   ├── wsgi.py                  # WSGI configuration
│   └── asgi.py                  # ASGI configuration
│
├── media/                       # User-uploaded media files
├── staticfiles/                 # Collected static files
├── venv/                        # Virtual environment
│
├── Drug.sol                     # Smart contract source code
├── Drug.json                    # Compiled smart contract
├── manage.py                    # Django management script
├── requirements.txt             # Python dependencies
├── Procfile                     # Deployment configuration
├── .gitignore                   # Git ignore rules
└── README.md                    # Project documentation
```

### Key Components

- **Smart Contracts**: `Drug.sol` contains the Ethereum smart contract for drug tracking
- **Django App**: `DrugTraceApp/` contains the main web application
- **Templates**: Role-specific templates for different stakeholders
- **Static Files**: CSS, JavaScript, and images for the web interface
- **Services**: Blockchain integration and business logic
- **Media**: Storage for user-uploaded files
- **Configuration**: Settings for both development and production environments 
