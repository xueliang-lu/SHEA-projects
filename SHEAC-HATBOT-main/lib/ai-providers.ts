import OpenAI from 'openai';
import { GoogleGenerativeAI } from '@google/generative-ai';

// Initialize OpenAI
const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
});

// Initialize Gemini
const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY || '');

export interface AIMessage {
    role: 'user' | 'assistant' | 'system';
    content: string;
}

export interface AIResponse {
    content: string;
    provider: 'openai' | 'gemini';
}

/**
 * Generate AI response using OpenAI
 */
export async function generateOpenAIResponse(
    messages: AIMessage[],
    systemPrompt?: string
): Promise<string> {
    try {
        const formattedMessages: OpenAI.Chat.ChatCompletionMessageParam[] = [];

        if (systemPrompt) {
            formattedMessages.push({
                role: 'system',
                content: systemPrompt,
            });
        }

        formattedMessages.push(
            ...messages.map((msg) => ({
                role: msg.role as 'user' | 'assistant' | 'system',
                content: msg.content,
            }))
        );

        const completion = await openai.chat.completions.create({
            model: 'gpt-4o-mini',
            messages: formattedMessages,
            temperature: 0.7,
            max_tokens: 1000,
        });

        return completion.choices[0]?.message?.content || 'No response generated';
    } catch (error: any) {
        console.error('OpenAI API Error:', error);
        // Fallback for demo/testing if quota exceeded or key missing
        // Return the API error as the assistant's response
        return `OpenAI API Error: ${error?.message || 'Unknown error'}`;
    }
}

/**
 * Generate AI response using Gemini
 */
export async function generateGeminiResponse(
    messages: AIMessage[],
    systemPrompt?: string
): Promise<string> {
    try {
        const model = genAI.getGenerativeModel({ model: 'gemini-2.0-flash' });

        // Build conversation history for Gemini
        const history = messages.slice(0, -1).map((msg) => ({
            role: msg.role === 'assistant' ? 'model' : 'user',
            parts: [{ text: msg.content }],
        }));

        const chatConfig: any = {
            history,
            generationConfig: {
                temperature: 0.7,
                maxOutputTokens: 1000,
            },
        };

        // Only add systemInstruction if it exists and is not empty
        if (systemPrompt && systemPrompt.trim()) {
            chatConfig.systemInstruction = {
                parts: [{ text: systemPrompt }],
                role: 'user'
            };
        }

        const chat = model.startChat(chatConfig);

        const lastMessage = messages[messages.length - 1];
        const result = await chat.sendMessage(lastMessage.content);
        const response = await result.response;

        return response.text() || 'No response generated';
    } catch (error: any) {
        console.error('Gemini API Error:', error);
        // Fallback for demo/testing
        // Return the API error as the assistant's response
        return `Gemini API Error: ${error?.message || 'Unknown error'}`;
    }
}

/**
 * Generate AI response using the specified provider
 */
export async function generateAIResponse(
    provider: 'openai' | 'gemini',
    messages: AIMessage[],
    systemPrompt?: string
): Promise<AIResponse> {
    let content: string;

    if (provider === 'openai') {
        content = await generateOpenAIResponse(messages, systemPrompt);
    } else {
        content = await generateGeminiResponse(messages, systemPrompt);
    }

    return {
        content,
        provider,
    };
}
