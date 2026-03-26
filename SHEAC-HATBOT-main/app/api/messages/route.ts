import { NextRequest, NextResponse } from 'next/server';
import connectDB from '@/lib/mongodb';
import Message from '@/models/Message';
import Conversation from '@/models/Conversation';
import { generateAIResponse, AIMessage } from '@/lib/ai-providers';
import { getRelevantFAQs, buildRAGContext } from '@/lib/rag';

const GUEST_USER_ID = 'guest';

export async function POST(req: NextRequest) {
    try {
        const { conversationId, content, aiProvider } = await req.json();

        if (!content) {
            return NextResponse.json({ error: 'Message content is required' }, { status: 400 });
        }

        await connectDB();

        let targetConversationId = conversationId;

        // Create a new conversation if no ID is provided
        if (!targetConversationId) {
            const newConversation = await Conversation.create({
                userId: GUEST_USER_ID,
                title: content.substring(0, 50) + (content.length > 50 ? '...' : ''),
            });
            targetConversationId = newConversation._id.toString();
        }

        // Save user message
        const userMessage = await Message.create({
            conversationId: targetConversationId,
            role: 'user',
            content,
        });

        // RAG Logic: Get relevant FAQs
        const relevantFAQs = await getRelevantFAQs(content);
        const ragContext = buildRAGContext(relevantFAQs);

        // Get conversation history for context (last 10 messages)
        const history = await Message.find({ conversationId: targetConversationId })
            .sort({ createdAt: -1 })
            .limit(10);

        // Sort history to chronological order and format for AI
        const formattedHistory: AIMessage[] = history
            .reverse()
            .map(msg => ({
                role: msg.role === 'assistant' ? 'assistant' : 'user',
                content: msg.content
            }));

        // Generate AI response
        const systemPrompt = `You are a helpful AI assistant. ${ragContext}`;
        const aiResponse = await generateAIResponse(
            aiProvider || 'openai',
            formattedHistory,
            systemPrompt
        );

        // Save AI message
        const assistantMessage = await Message.create({
            conversationId: targetConversationId,
            role: 'assistant',
            content: aiResponse.content,
            aiProvider: aiResponse.provider,
        });

        // Update conversation lastMessageAt
        await Conversation.findByIdAndUpdate(targetConversationId, {
            lastMessageAt: new Date(),
        });

        return NextResponse.json({
            userMessage,
            assistantMessage,
            conversationId: targetConversationId
        }, { status: 201 });
    } catch (error: any) {
        console.error('Send message error:', error);
        return NextResponse.json({ error: error?.message || 'Internal server error' }, { status: 500 });
    }
}
