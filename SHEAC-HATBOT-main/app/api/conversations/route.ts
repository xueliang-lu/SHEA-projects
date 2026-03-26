import { NextRequest, NextResponse } from 'next/server';
import connectDB from '@/lib/mongodb';
import Conversation from '@/models/Conversation';

const GUEST_USER_ID = 'guest';

export async function GET() {
    try {
        await connectDB();

        const conversations = await Conversation.find({ userId: GUEST_USER_ID })
            .sort({ lastMessageAt: -1 });

        return NextResponse.json(conversations);
    } catch (error: any) {
        console.error('Fetch conversations error:', error);
        return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
    }
}

export async function POST(req: NextRequest) {
    try {
        const { title } = await req.json();

        await connectDB();

        const conversation = await Conversation.create({
            userId: GUEST_USER_ID,
            title: title || 'New Conversation',
        });

        return NextResponse.json(conversation, { status: 201 });
    } catch (error: any) {
        console.error('Create conversation error:', error);
        return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
    }
}
