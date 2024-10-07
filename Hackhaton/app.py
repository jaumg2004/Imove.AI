from flask import Flask, request, jsonify, render_template
import requests
import json
import googlemaps
import pandas as pd
import numpy as np
import time
import random
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import LabelEncoder

app = Flask(__name__, template_folder='Template')

# Chaves das APIs
GOOGLE_MAPS_API_KEY = 'SUA CHAVE API DO GOOGLE MAPS'
CRIMEOMETER_API_KEY = 'SUA CHAVE API DA CRIMEOMETER'
OPENAI_API_KEY = 'SUA CHAVE API DA OPENAI'

gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
previous_messages = []

# Função do chatbot
def fetch_response_from_api(user_input):
    url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {OPENAI_API_KEY}'
    }
    body = {
        'model': 'gpt-3.5-turbo',
        'messages': [
            {
                'role': 'system',
                'content': '''
                Você é um assistente virtual inteligente para suporte ao cliente especializado no mercado imobiliário. Sua função é responder perguntas comuns sobre compra, venda e aluguel de imóveis, além de ajudar os usuários com processos relacionados.
                Siga as seguintes diretrizes:
                1. Após a pessoa mandar a primeira mensagem, você deve se apresentar falando seu nome, dizendo que você é o ChatBot de Suporte, assistente de suporte imobiliário. Diga isso de forma amigável e pergunte como pode ajudar.
                2. Responda de forma educada e objetiva a perguntas sobre compra, venda ou aluguel de propriedades.
                3. Dê informações claras sobre documentos necessários, prazos, taxas comuns e passos gerais do processo de compra ou venda de imóveis.
                4. Ao falar de aluguel, explique questões como contrato, caução, fiadores e valor de mercado.
                5. Caso o usuário faça uma pergunta complexa ou que você não tenha as informações exatas, ofereça-se para encaminhar a questão para um agente humano.
                6. Sempre passe um ar profissional e amigável, tentando ser o mais útil possível para facilitar a jornada do cliente.
                '''
            },
            *previous_messages,
            {'role': 'user', 'content': user_input}
        ]
    }

    # Envia a solicitação para a API do OpenAI
    response = requests.post(url, headers=headers, data=json.dumps(body))
    response_data = response.json()

    # Retorna a resposta do assistente
    response_content = response_data['choices'][0]['message']['content'].strip()

    # Simula o tempo de digitação (por exemplo, 2 segundos)
    typing_delay = random.uniform(1, 3)  # Tempo de espera aleatório entre 1 e 3 segundos
    time.sleep(typing_delay)

    return response_content

# Funções para obter dados de localização e segurança
def get_location_data(address):
    geocode_result = gmaps.geocode(address)
    if geocode_result:
        location = geocode_result[0]['geometry']['location']
        return location['lat'], location['lng']
    return None, None

def get_crime_data(lat, lng):
    crime_api_url = f'https://api.crimeometer.com/v1/incidents/raw-data?lat={lat}&lon={lng}&distance=1mi&datetime_ini=2023-01-01T00:00:00Z&datetime_end=2023-12-31T23:59:59Z'
    headers = {'x-api-key': CRIMEOMETER_API_KEY}
    response = requests.get(crime_api_url, headers=headers)
    return len(response.json().get('incidents', [])) if response.status_code == 200 else 0

def get_policing_data(lat, lng):
    try:
        policing_api_url = f'https://api.exemplo.com/v1/policing?lat={lat}&lng={lng}'  # Substitua pela URL correta
        response = requests.get(policing_api_url)

        if response.status_code == 200:
            policing_data = response.json()
            return policing_data.get('presence', 0)
        else:
            print(f"Erro ao acessar dados de policiamento: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao fazer a requisição para a API de policiamento: {e}")
    return 0

def get_neighborhood_quality(lat, lng):
    places_result = gmaps.places_nearby(location=(lat, lng), radius=1000, type='park')
    return len(places_result.get('results', []))

# Rotas Flask
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/prever_preco', methods=['POST'])
def prever_preco():
    base = pd.read_csv(r'C:\Users\Jaum\Downloads\imoveis.csv')
    base = base.drop(['Unnamed'], axis=1)
    y = base['price'].values
    X = base.drop('price', axis=1).values
    labelencoder = LabelEncoder()
    for i in range(X.shape[1]):
        if isinstance(X[0, i], str):
            X[:, i] = labelencoder.fit_transform(X[:, i])
    X_treinamento, X_teste, y_treinamento, y_teste = train_test_split(X, y, test_size=0.3, random_state=1)
    modelo = RandomForestRegressor(random_state=1, n_estimators=500, max_depth=10, max_leaf_nodes=8)
    modelo.fit(X_treinamento, y_treinamento)

    # Receber dados do frontend
    data = request.json
    nova_entrada = np.array([[data['quartos'], data['banheiros'], data['area'], data['garagem']]])
    previsao_novo_imovel = modelo.predict(nova_entrada)

    return jsonify({'previsao': round(previsao_novo_imovel[0], 2)})

@app.route('/analisar_seguranca', methods=['POST'])
def analisar_seguranca():
    address = request.json.get('address')
    lat, lng = get_location_data(address)
    if lat and lng:
        crime_rate = get_crime_data(lat, lng)
        policing_presence = get_policing_data(lat, lng)
        neighborhood_quality = get_neighborhood_quality(lat, lng)

        # Carregar a base de dados de segurança
        base = pd.read_csv('C:/Users/Jaum/Downloads/classificacao_seguranca.csv')
        base['taxas de criminalidade'] = crime_rate
        base['presença de policiamento'] = policing_presence
        base['qualidade da vizinhança'] = neighborhood_quality
        base = base.drop(['Unnamed'], axis=1) if 'Unnamed' in base.columns else base

        y = base['classificação de segurança'].values
        X = base.drop('classificação de segurança', axis=1).values
        labelencoder = LabelEncoder()
        for i in range(X.shape[1]):
            if isinstance(X[0, i], str):
                X[:, i] = labelencoder.fit_transform(X[:, i])
        X_treinamento, X_teste, y_treinamento, y_teste = train_test_split(X, y, test_size=0.3, random_state=1)
        modelo = RandomForestClassifier(random_state=1, n_estimators=500, max_depth=10, max_leaf_nodes=8)
        modelo.fit(X_treinamento, y_treinamento)
        previsao_analise_de_seguranca = modelo.predict(np.array([[crime_rate, policing_presence, neighborhood_quality]]))

        return jsonify({'previsao_seguranca': previsao_analise_de_seguranca[0]})
    else:
        return jsonify({'error': 'Endereço não encontrado.'}), 404

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message')
    previous_messages.append({'role': 'user', 'content': user_input})
    assistant_response = fetch_response_from_api(user_input)
    previous_messages.append({'role': 'assistant', 'content': assistant_response})
    return jsonify({'response': assistant_response})

if __name__ == '__main__':
    app.run(debug=True)
