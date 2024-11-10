def get_valid_number():
    while True:
        try:
            num = int(input("Inserisci il numero di messaggi da inviare: "))
            if num > 0:
                return num
            print("Per favore inserisci un numero maggiore di 0.")
        except ValueError:
            print("Per favore inserisci un numero valido.")

def setup_config(parser_class):
    while True:
        url = input("\nInserisci l'URL del profilo NGL (es. https://ngl.link/username): ")
        parser = parser_class(url)
        
        print("\nRecupero informazioni dalla pagina...")
        if parser.fetch_page() and parser.extract_data():
            return parser.get_config()
        
        retry = input("\nErrore nel recupero delle informazioni. Vuoi riprovare? (s/n): ")
        if retry.lower() != 's':
            return None 