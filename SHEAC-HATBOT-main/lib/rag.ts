import OpenAI from 'openai';
import FAQ from '@/models/FAQ';
import connectDB from './mongodb';

const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
});

/**
 * Generate embedding for a given text using OpenAI
 */
export async function generateEmbedding(text: string): Promise<number[]> {
    try {
        const response = await openai.embeddings.create({
            model: 'text-embedding-3-small',
            input: text.replace(/\n/g, ' '),
        });
        return response.data[0].embedding;
    } catch (error) {
        console.error('Error generating embedding:', error);
        throw new Error('Failed to generate embedding');
    }
}

/**
 * Calculate cosine similarity between two vectors
 */
export function cosineSimilarity(vecA: number[], vecB: number[]): number {
    const dotProduct = vecA.reduce((sum, val, i) => sum + val * vecB[i], 0);
    const magnitudeA = Math.sqrt(vecA.reduce((sum, val) => sum + val * val, 0));
    const magnitudeB = Math.sqrt(vecB.reduce((sum, val) => sum + val * val, 0));
    if (magnitudeA === 0 || magnitudeB === 0) return 0;
    return dotProduct / (magnitudeA * magnitudeB);
}

/**
 * Retrieve relevant FAQs for a given query
 */
export async function getRelevantFAQs(query: string, limit: number = 3) {
    await connectDB();

    try {
        const queryEmbedding = await generateEmbedding(query);

        // In a real production app with many FAQs, you'd use a vector database
        // For small FAQ sets, we can fetch all and rank manually or use MongoDB Atlas Vector Search
        const faqs = await FAQ.find({ embedding: { $exists: true, $ne: [] } });

        const rankedFAQs = faqs
            .map(faq => ({
                question: faq.question,
                answer: faq.answer,
                similarity: cosineSimilarity(queryEmbedding, faq.embedding!)
            }))
            .sort((a, b) => b.similarity - a.similarity)
            .slice(0, limit);

        // Only return FAQs that are relevant (similarity > 0.3)
        return rankedFAQs.filter(faq => faq.similarity > 0.3);
    } catch (error) {
        console.error('Error retrieving relevant FAQs:', error);
        return [];
    }
}

/**
 * Build a system prompt context from relevant FAQs
 */
export function buildRAGContext(relevantFAQs: any[]) {
    if (relevantFAQs.length === 0) return '';

    let context = "Here is some relevant information from our FAQ database to help you answer the user's question:\n\n";

    relevantFAQs.forEach((faq, index) => {
        context += `FAQ ${index + 1}:\nQuestion: ${faq.question}\nAnswer: ${faq.answer}\n\n`;
    });

    context += "Please use this information if relevant to provide an accurate answer. If the information doesn't help, answer normally based on your knowledge.";

    return context;
}
