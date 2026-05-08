# 📱 SMS Platform - Números Temporários para Receber SMS

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-teal)
![License](https://img.shields.io/badge/license-MIT-orange)

## ✨ Sobre o Projeto

**SMS Platform** é uma plataforma web completa que permite aos usuários obter números de telefone temporários para receber SMS de verificação, ativações de conta e muito mais. Desenvolvida com **FastAPI** e **SQLite**, oferece uma experiência moderna, segura e totalmente responsiva.

### 🎯 Funcionalidades Principais

- ✅ **Autenticação completa** - Registro, login e logout seguro
- ✅ **Números temporários** - Adquira números de diversos países
- ✅ **Gerenciamento de SMS** - Receba e visualize mensagens em tempo real
- ✅ **Painel de controle** - Estatísticas e visão geral da sua conta
- ✅ **Design moderno** - Tema escuro inspirado no WhatsApp Beta Black
- ✅ **100% Responsivo** - Funciona perfeitamente em mobile, tablet e desktop
- ✅ **Sistema de planos** - Gratuito e Premium com benefícios exclusivos

### 🌍 Países Suportados

| Código | País | Código | País |
|--------|------|--------|------|
| 🇺🇸 US | Estados Unidos | 🇬🇧 UK | Reino Unido |
| 🇧🇷 BR | Brasil | 🇨🇦 CA | Canadá |
| 🇦🇺 AU | Austrália | 🇩🇪 DE | Alemanha |
| 🇫🇷 FR | França | 🇪🇸 ES | Espanha |
| 🇮🇹 IT | Itália | 🇵🇹 PT | Portugal |

## 🚀 Tecnologias Utilizadas

### Backend
- **FastAPI** - Framework web moderno e rápido
- **SQLAlchemy** - ORM para banco de dados
- **SQLite** - Banco de dados leve e integrado
- **JWT** - Autenticação segura via tokens
- **AIOHTTP** - Cliente HTTP assíncrono

### Frontend
- **TailwindCSS** - Framework CSS utilitário
- **Boxicons** - Biblioteca de ícones moderna
- **Inter Font** - Tipografia moderna e legível

## 📦 Instalação e Execução Local

### Pré-requisitos
- Python 3.10 ou superior
- Git (opcional)

### Passo a Passo

1. **Clone o repositório**
```bash
git clone https://github.com/seu-usuario/sms-platform.git
cd sms-platform
```

2. **Crie um ambiente virtual**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. **Instale as dependências**
```bash
pip install -r requirements.txt
```

4. **Execute a aplicação**
```bash
python app.py
# ou
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

5. **Acesse no navegador**
```
http://localhost:8000
```

## 🎨 Estrutura do Projeto

```
sms-platform/
├── app.py                 # Aplicação principal FastAPI
├── requirements.txt       # Dependências do projeto
├── database.db           # Banco de dados SQLite (criado automaticamente)
├── templates/            # Templates HTML
│   ├── index.html        # Página inicial
│   ├── register.html     # Cadastro de usuário
│   ├── login.html        # Login de usuário
│   ├── dashboard.html    # Painel de controle
│   ├── numbers.html      # Gerenciamento de números
│   ├── messages.html     # Visualização de SMS
│   └── profile.html      # Perfil do usuário
└── README.md             # Documentação
```

## 🔒 Funcionalidades de Segurança

- ✅ **Hash de senhas** com SHA256 + Salt
- ✅ **Tokens JWT** para autenticação
- ✅ **Proteção de rotas** exclusivas para usuários autenticados
- ✅ **Cookies seguros** (HttpOnly)
- ✅ **Validação de dados** em formulários

## 📊 Planos Disponíveis

### 🆓 Plano Gratuito
- Até 5 números simultâneos
- Números válidos por 7 dias
- Suporte padrão

### 💎 Plano Premium (Em breve)
- Até 20 números simultâneos
- Números válidos por 30 dias
- Suporte prioritário 24/7
- Sem anúncios

## 🖼️ Screenshots

| Página | Descrição |
|--------|-----------|
| 🏠 Home | Landing page com apresentação do serviço |
| 📝 Cadastro | Formulário de criação de conta |
| 🔐 Login | Autenticação de usuários |
| 📊 Dashboard | Visão geral com estatísticas |
| 📞 Números | Gerenciamento de números adquiridos |
| 💬 Mensagens | Visualização de SMS recebidos |

## 🌐 Deploy

### Render.com (Recomendado - Gratuito)

1. Crie uma conta em [render.com](https://render.com)
2. Conecte seu repositório do GitHub
3. Configure o serviço:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app:app --host 0.0.0.0 --port $PORT`
4. Clique em **"Create Web Service"**

### Ngrok (Testes rápidos)

```bash
ngrok http 8000
```

## 🤝 Contribuição

Contribuições são bem-vindas! Siga os passos:

1. Faça um **Fork** do projeto
2. Crie uma **branch** para sua feature (`git checkout -b feature/AmazingFeature`)
3. **Commit** suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. **Push** para a branch (`git push origin feature/AmazingFeature`)
5. Abra um **Pull Request**

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 👨‍💻 Desenvolvido por

**Nexus Platform** por **© LucasDesigner**

- 💼 Portfólio: [Seu site]
- 📧 Email: [seu email]
- 🐙 GitHub: [seu usuário]

## 🙏 Agradecimentos

- [FastAPI](https://fastapi.tiangolo.com/) - Framework incrível
- [TailwindCSS](https://tailwindcss.com/) - CSS utility-first
- [Boxicons](https://boxicons.com/) - Ícones gratuitos
- [Online-SMS](https://online-sms.org) - API de números temporários

---

⭐️ **Não esqueça de dar uma estrela no projeto!** ⭐️

Desenvolvido com ❤️ para sua privacidade