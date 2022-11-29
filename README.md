### Installation and running

1. Clone the repo
   ```sh
   git clone https://github.com/galtet/documents_search.git
   ```
2. Run using docker compose
   ```sh
   docker-compose up -d
   ```
3. Load the data (loading all the documents)
   ```sh
   python3 load_data.py
   ```
4. Start using it through swagger - go to: http://localhost:5004/apidocs
