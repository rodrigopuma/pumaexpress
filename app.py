import streamlit as st
import mercadopago
import requests  # Adicionamos esta biblioteca para chamar o Telegram

# --- CONFIGURAÇÕES ---
# Pegamos as chaves dos secrets (Lembre-se de adicionar no secrets.toml)
try:
    ACCESS_TOKEN = st.secrets["MP_ACCESS_TOKEN"]
    sdk = mercadopago.SDK(ACCESS_TOKEN)
    
    # NOVAS CONFIGURAÇÕES DO TELEGRAM
    TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"] # O token do BotFather
    TELEGRAM_CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"] # O seu ID numérico
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
    """Envia uma mensagem automática para o seu Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensagem,
        "parse_mode": "Markdown" # Permite usar negrito
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print("Erro ao enviar Telegram:", e)

# --- FRONTEND E LÓGICA ---
st.set_page_config(page_title="PontoLabs Express", layout="centered")

st.title("⚡ PontoLabs Express")
st.write("Escolha seu kit de sobrevivência:")

cardapio = {"Energético": 10.00, "Coca-Cola (Lata)": 6.00, "Chocolate": 4.00}
carrinho = {}

for item, preco in cardapio.items():
    col1, col2 = st.columns([2, 1])
    col1.write(f"**{item}** - R$ {preco:.2f}")
    qtd = col2.number_input(f"Qtd_{item}", min_value=0, max_value=10, key=item, label_visibility="collapsed")
    if qtd > 0:
        carrinho[item] = qtd

if st.button("Gerar Pagamento Pix"):
    if not carrinho:
        st.warning("O carrinho está vazio.")
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

# --- FLUXO DE PAGAMENTO E NOTIFICAÇÃO ---
if "payment_id" in st.session_state:
    st.divider()
    st.subheader("Pagamento via Pix")
    st.image(f"data:image/jpeg;base64,{st.session_state.qr_code_base64}", caption="Leia o QR Code no app do seu banco")
    st.code(st.session_state.qr_code, language="text")
    
    st.info("O sistema verificará seu pagamento automaticamente. Ou clique abaixo para checar agora.")
    
    if st.button("Verificar Pagamento"):
        with st.spinner("Consultando banco..."):
            estado = sdk.payment().get(st.session_state.payment_id)["response"]["status"]
        
        if estado == "approved":
            st.success("✅ Pagamento Aprovado! Estamos preparando o seu pedido.")
            st.balloons()
            
            # --- O SISTEMA AVISA VOCÊ AUTOMATICAMENTE ---
            msg_alerta = f"🚨 *NOVO PEDIDO PAGO!*\n\n📦 *Itens:* {st.session_state.resumo}\n💰 *Valor:* R$ {st.session_state.total:.2f}\n\n_Bora entregar, guerreiro!_"
            enviar_notificacao_telegram(msg_alerta)
            
            # Limpa o ID para o próximo pedido
            del st.session_state.payment_id
        else:
            st.warning("⏳ Pagamento ainda não caiu. Se já pagou, espere uns segundos.")