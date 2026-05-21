import os
import urllib.request
import zipfile

def baixar_e_extrair_dados():
    url = "https://www.camara.leg.br/cotas/Ano-2024.csv.zip"
    zip_path = "Ano-2024.zip"
    csv_filename = "Ano-2024.csv"
    
    print(f"Baixando dados de {url}...")
    urllib.request.urlretrieve(url, zip_path)
    print("Download concluído. Extraindo arquivo...")
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(".")
    
    # Remove o arquivo ZIP após extrair para limpar a pasta
    if os.path.exists(zip_path):
        os.remove(zip_path)
        
    print(f"Arquivo extraído com sucesso: {csv_filename}")
    print("A coleta foi finalizada. O dataset agora pode ser consumido pelo dashboard.")

if __name__ == "__main__":
    baixar_e_extrair_dados()
