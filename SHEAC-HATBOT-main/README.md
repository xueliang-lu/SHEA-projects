# SHEA Chatbot (SheaBot)

A modern AI chatbot application powered by **OpenAI GPT-4o** and **Google Gemini 2.0 Flash**, with a built-in **RAG (Retrieval Augmented Generation)** system for personalized FAQ knowledge base queries.

---

## ✨ Features

- **Dual AI Engines** — Toggle between OpenAI's GPT-4o-mini and Google's Gemini 2.0 Flash
- **FAQ Knowledge Base** — RAG system reads your FAQ documents to provide accurate, context-aware answers
- **Full Chat History** — Access, search, and manage all your conversations
- **Modern UI** — Clean, responsive interface built with Next.js 16 and Tailwind CSS
- **MongoDB Storage** — Persistent chat history and conversation management

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|------------|
| Framework | Next.js 16.1.6 (App Router) |
| Language | TypeScript 5 |
| Styling | Tailwind CSS 4 |
| AI Providers | OpenAI GPT-4o-mini, Google Gemini 2.0 Flash |
| Database | MongoDB (via Mongoose) |
| UI Components | React 19, react-markdown |

---

## 📁 Project Structure

```
SHEAC-HATBOT-main/
├── app/
│   ├── api/              # API routes
│   ├── chat/             # Chat interface pages
│   ├── components/       # Reusable UI components
│   ├── globals.css       # Global styles
│   ├── layout.tsx        # Root layout
│   └── page.tsx          # Landing page
├── lib/
│   ├── ai-providers.ts   # OpenAI & Gemini integration
│   ├── mongodb.ts        # Database connection
│   └── rag.ts            # RAG system logic
├── models/               # Mongoose models
├── types/                # TypeScript type definitions
├── data/                 # FAQ documents for RAG
├── public/               # Static assets
├── package.json
├── tsconfig.json
└── next.config.ts
```

---

## 🚀 Getting Started

### Prerequisites

- **Node.js** 20+ 
- **MongoDB** (local or cloud instance)
- **API Keys**:
  - OpenAI API Key
  - Google Gemini API Key

### 1. Clone the repository

```bash
git clone <repository-url>
cd SHEAC-HATBOT-main
```

### 2. Install dependencies

```bash
npm install
```

### 3. Set up environment variables

Create a `.env.local` file in the root directory:

```bash
# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Google Gemini
GEMINI_API_KEY=your_gemini_api_key

# MongoDB
MONGODB_URI=mongodb://localhost:27017/sheabot
# or for MongoDB Atlas:
# MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/sheabot
```

### 4. Run the development server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 📖 Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run start` | Start production server |
| `npm run lint` | Run ESLint |

---

## 🤖 AI Providers

### OpenAI (GPT-4o-mini)
- Fast, cost-effective responses
- Strong general-purpose capabilities
- Configured in `lib/ai-providers.ts`

### Google Gemini (gemini-2.0-flash)
- Google's latest flash model
- Excellent for structured outputs
- Alternative provider for redundancy

Switch between providers in the chat interface.

---

## 📚 RAG System

The Retrieval Augmented Generation system:

1. **Indexes** FAQ documents stored in `data/`
2. **Retrieves** relevant passages based on user queries
3. **Augments** AI prompts with context for accurate answers

To add new FAQ documents:
- Place markdown or text files in the `data/` folder
- The RAG system will automatically index them

---

## 💾 Database Schema

### Chat Collection
```typescript
{
  _id: ObjectId,
  userId: string,
  title: string,
  messages: [{
    role: 'user' | 'assistant',
    content: string,
    timestamp: Date,
    provider: 'openai' | 'gemini'
  }],
  createdAt: Date,
  updatedAt: Date
}
```

---

## 🔧 Configuration

### next.config.ts
Configure Next.js behavior, redirects, and security headers.

### tsconfig.json
TypeScript compiler options for the project.

### eslint.config.mjs
ESLint rules for code quality.

---

## 🌐 Deployment

### Vercel (Recommended)

The easiest way to deploy:

1. Push code to GitHub
2. Import project in [Vercel](https://vercel.com)
3. Add environment variables in Vercel dashboard
4. Deploy

### Docker

```bash
docker build -t sheabot .
docker run -p 3000:3000 --env-file .env.local sheabot
```

### Self-hosted

```bash
npm run build
npm run start
```

---

## 🐛 Troubleshooting

### MongoDB connection fails
- Verify `MONGODB_URI` is correct
- Ensure MongoDB is running
- Check network/firewall settings

### AI responses show errors
- Verify API keys are valid
- Check API quota/limits
- Review `lib/ai-providers.ts` for error messages

### RAG not finding documents
- Ensure files exist in `data/` folder
- Check file permissions
- Verify RAG indexing logic in `lib/rag.ts`

---

## 📝 Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key for GPT-4o |
| `GEMINI_API_KEY` | Yes | Google Gemini API key |
| `MONGODB_URI` | Yes | MongoDB connection string |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is private and proprietary.

---

## 👨‍💻 Author

**Sunil Paudel**
**Xueliang Lu**

---

## 🙏 Acknowledgments

- [Next.js](https://nextjs.org)
- [OpenAI](https://openai.com)
- [Google Generative AI](https://ai.google)
- [Tailwind CSS](https://tailwindcss.com)
- [MongoDB](https://mongodb.com)
