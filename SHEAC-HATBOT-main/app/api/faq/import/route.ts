import { NextRequest, NextResponse } from 'next/server';
import connectDB from '@/lib/mongodb';
import FAQ from '@/models/FAQ';
import { generateEmbedding } from '@/lib/rag';
import fs from 'fs';
import path from 'path';

export async function POST(req: NextRequest) {
    try {
        const { filePath } = await req.json();
        const absolutePath = path.resolve(process.cwd(), filePath || 'data/faqs.json');

        if (!fs.existsSync(absolutePath)) {
            return NextResponse.json({ error: 'FAQ file not found at ' + absolutePath }, { status: 404 });
        }

        const fileContent = fs.readFileSync(absolutePath, 'utf8');
        const faqs = JSON.parse(fileContent);

        await connectDB();

        console.log(`Starting import of ${faqs.length} FAQs...`);

        for (const item of faqs) {
            if (!item.question || !item.answer) continue;

            // Generate embedding for the question
            const embedding = await generateEmbedding(item.question);

            // Create or update FAQ
            await FAQ.findOneAndUpdate(
                { question: item.question },
                {
                    answer: item.answer,
                    embedding,
                    category: item.category || 'General'
                },
                { upsert: true }
            );
        }

        return NextResponse.json({ message: `Successfully imported ${faqs.length} FAQs with embeddings.` });
    } catch (error: any) {
        console.error('FAQ import error:', error);
        return NextResponse.json({ error: error.message || 'Internal server error' }, { status: 500 });
    }
}
