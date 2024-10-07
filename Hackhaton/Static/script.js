document.getElementById('send_btn').addEventListener('click', function() {
    let userInput = document.getElementById('user_input').value;
    fetch('/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message: userInput})
    })
        .then(response => response.json())
        .then(data => {
            let chatbox = document.getElementById('chatbox');
            chatbox.innerHTML += `<p>User: ${userInput}</p>`;
            chatbox.innerHTML += `<p>Bot: ${data.response}</p>`;
            document.getElementById('user_input').value = '';
        });
});

document.getElementById('predict_price_btn').addEventListener('click', function() {
    let quartos = document.getElementById('quartos').value;
    let banheiros = document.getElementById('banheiros').value;
    let area = document.getElementById('area').value;
    let garagem = document.getElementById('garagem').value;

    fetch('/prever_preco', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({quartos, banheiros, area, garagem})
    })
        .then(response => response.json())
        .then(data => {
            document.getElementById('predicted_price').innerHTML = `Preço Estimado: R$${data.previsao}`;
        });
});

document.getElementById('analyze_safety_btn').addEventListener('click', function() {
    let address = document.getElementById('address').value;

    fetch('/analisar_seguranca', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({address})
    })
        .then(response => response.json())
        .then(data => {
            if (data.previsao_seguranca) {
                document.getElementById('safety_analysis').innerHTML = `Classificação de Segurança: ${data.previsao_seguranca}`;
            } else {
                document.getElementById('safety_analysis').innerHTML = `Erro: Endereço não encontrado.`;
            }
        });
});
