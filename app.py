import streamlit as st

# Configuração da página para estilo mobile e azul escuro
st.set_page_config(page_title="Puma Express", page_icon="⚡", layout="centered")

# Estilização CSS personalizada (Azul Escuro)
st.markdown('''
    <style>
    .stApp {
        background-color: #0A192F;
        color: white;
    }
    h1, h2, h3 {
        color: #64FFDA;
    }
    .stButton>button {
        background-color: #64FFDA;
        color: #0A192F;
        font-weight: bold;
        border-radius: 10px;
    }
    .stNumberInput>div>div>input {
        background-color: #112240;
        color: white;
    }
    </style>
''', unsafe_allow_html=True)

# Título e Cardápio
st.title("⚡ Puma Express")
st.write("Selecione seus itens e peça direto no WhatsApp")

cardapio = {
    "Energético": 10.00,
    "Coca-Cola (Lata)": 6.00,
    "Água Mineral": 3.00,
    "Chocolate": 4.00
}

carrinho = {}

for item, preco in cardapio.items():
    col1, col2 = st.columns([2, 1])
    col1.markdown(f"**{item}**<br>R$ {preco:.2f}", unsafe_allow_html=True)
    qtd = col2.number_input("", min_value=0, max_value=10, key=item)
    if qtd > 0:
        carrinho[item] = qtd

# Finalização
if st.button("Finalizar Pedido"):
    if not carrinho:
        st.warning("Seu carrinho está vazio!")
    else:
        total = sum(cardapio[item] * qtd for item, qtd in carrinho.items())
        itens_resumo = ", ".join([f"{qtd}x {item}" for item, qtd in carrinho.items()])
        mensagem = f"Olá, gostaria de fazer um pedido no PumaExpress: {itens_resumo}. Total: R$ {total:.2f}"
        
        # Link para WhatsApp
        wa_link = f"https://wa.me/5581986302122?text={mensagem.replace(' ', '%20')}"
        
        st.success(f"### Total: R$ {total:.2f}")
        st.markdown(f"### [Clique aqui para enviar o pedido no WhatsApp]({wa_link})", unsafe_allow_html=True)
        st.info("Aguardando confirmação do pagamento via Pix.")