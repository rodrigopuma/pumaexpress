import streamlit as st
import mercadopago
import requests
import time  # <-- IMPORTANTE: Adicionado para fazer o sistema esperar e atualizar sozinho

# --- CONFIGURAÇÕES ---
try:
    ACCESS_TOKEN = st.secrets["MP_ACCESS_TOKEN"]
    sdk = mercadopago.SDK(ACCESS_TOKEN)
    
    TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
    TELEGRAM_CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
except Exception as e:
    st.error("Erro ao carregar os Secrets. Verifique o arquivo .streamlit/secrets.toml")

# --- FUNÇÕES ---
def criar_pagamento_pix(valor, descricao, email_cliente="cliente@email.com"):
    payment_data = {
        "transaction_amount": float(valor),
        "description": descricao,
        "payment_method_id": "pix",
        "payer": {
            "email": email_cliente,
        }
    }
    result = sdk.payment().create(payment_data)
    return result["response"]

def enviar_notificacao_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensagem,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print("Erro ao enviar Telegram:", e)

# --- FRONTEND E LÓGICA ---
st.set_page_config(page_title="PontoLabs Express", layout="centered")

st.title("⚡ PontoLabs Express")
st.write("Escolha seu kit de sobrevivência:")

cardapio = {"Energético": 10.00, "Coca-Cola (Lata)": 6.00, "Chocolate": 4.00, "Mix de Açai": 0.01}
carrinho = {}

# Exibe os produtos
for item, preco in cardapio.items():
    col1, col2 = st.columns([2, 1])
    col1.write(f"**{item}** - R$ {preco:.2f}")
    qtd = col2.number_input(f"Qtd_{item}", min_value=0, max_value=10, key=item, label_visibility="collapsed")
    if qtd > 0:
        carrinho[item] = qtd

st.divider()
# NOVO: Pergunta onde o cliente está
local_entrega = st.text_input("📍 Onde você está? (Ex: Corpo da Guarda, Alojamento 2):", placeholder="Local de entrega")

if st.button("Gerar Pagamento Pix"):
    if not carrinho:
        st.warning("O carrinho está vazio.")
    elif not local_entrega:
        st.warning("Por favor, informe onde você está para podermos entregar!")
    else:
        total = sum(cardapio[item] * qtd for item, qtd in carrinho.items())
        resumo = ", ".join([f"{qtd}x {item}" for item, qtd in carrinho.items()])
        
        with st.spinner("A gerar o seu Pix..."):
            resposta_pix = criar_pagamento_pix(total, f"Pedido: {resumo}")
            
            if "id" in resposta_pix:
                st.session_state.payment_id = resposta_pix["id"]
                st.session_state.qr_code_base64 = resposta_pix["point_of_interaction"]["transaction_data"]["qr_code_base64"]
                st.session_state.qr_code = resposta_pix["point_of_interaction"]["transaction_data"]["qr_code"]
                st.session_state.resumo = resumo
                st.session_state.total = total
                st.session_state.local = local_entrega  # Salva o local

# --- FLUXO DE PAGAMENTO AUTOMÁTICO ---
if "payment_id" in st.session_state:
    st.divider()
    st.subheader("Pagamento via Pix")
    st.image(f"data:image/jpeg;base64,{st.session_state.qr_code_base64}", caption="Leia o QR Code no app do seu banco")
    st.code(st.session_state.qr_code, language="text")
    
    # Criamos um espaço vazio no site que vai ser atualizado sozinho
    status_placeholder = st.empty()
    
    pagamento_confirmado = False
    
    # LOOP DE VERIFICAÇÃO: Vai checar a cada 5 segundos (por até 5 minutos)
    for i in range(60): 
        try:
            resposta = sdk.payment().get(st.session_state.payment_id)
            estado = resposta["response"]["status"]
        except Exception:
            estado = "pending" # Se der erro de internet, ignora e tenta de novo

        if estado == "approved":
            pagamento_confirmado = True
            break
            
        # Atualiza a mensagem na tela para o cliente saber que está rodando
        status_placeholder.info("⏳ Processando... Realize o pagamento. O sistema atualizará automaticamente assim que o dinheiro cair.")
        time.sleep(5) # Espera 5 segundos antes de perguntar ao Mercado Pago de novo
        
    # --- RESULTADO FINAL ---
    if pagamento_confirmado:
        status_placeholder.success("✅ Pagamento Aprovado! Estamos preparando o seu pedido.")
        st.balloons()
        
        # Telegram recebe a mensagem completa com o Local!
        msg_alerta = f"🚨 *NOVO PEDIDO PAGO!*\n\n📍 *Local:* {st.session_state.local}\n📦 *Itens:* {st.session_state.resumo}\n💰 *Valor:* R$ {st.session_state.total:.2f}\n\n_Bora entregar, guerreiro!_"
        enviar_notificacao_telegram(msg_alerta)
        
        # Apaga o pagamento da memória para o cliente poder pedir outra vez depois
        del st.session_state.payment_id
    else:
        # Se passar 5 minutos e não pagar, ele cancela
        status_placeholder.error("❌ Tempo limite de 5 minutos excedido. Faça o pedido novamente se ainda desejar.")
        del st.session_state.payment_id
        if st.button("Tentar Novamente"):
            st.rerun()