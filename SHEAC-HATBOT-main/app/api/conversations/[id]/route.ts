import { NextRequest, NextResponse } from 'next/server';
import connectDB from '@/lib/mongodb';
import Conversation from '@/models/Conversation';
import Message from '@/models/Message';

const GUEST_USER_ID = 'guest';

export async function GET(
    req: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id } = await params;

        await connectDB();

        const conversation = await Conversation.findOne({
            _id: id,
            userId: GUEST_USER_ID,
        });

        if (!conversation) {
            return NextResponse.json({ error: 'Conversation not found' }, { status: 404 });
        }

        const messages = await Message.find({ conversationId: id }).sort({ createdAt: 1 });

        return NextResponse.json({ ...conversation.toObject(), messages });
    } catch (error: any) {
        console.error('Fetch conversation error:', error);
        return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
    }
}

export async function PATCH(
    req: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id } = await params;
        const { title } = await req.json();

        await connectDB();

        const conversation = await Conversation.findOneAndUpdate(
            { _id: id, userId: GUEST_USER_ID },
            { title },
            { new: true }
        );

        if (!conversation) {
            return NextResponse.json({ error: 'Conversation not found' }, { status: 404 });
        }

        return NextResponse.json(conversation);
    } catch (error: any) {
        console.error('Update conversation error:', error);
        return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
    }
}

export async function DELETE(
    req: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id } = await params;

        await connectDB();

        const conversation = await Conversation.findOneAndDelete({
            _id: id,
            userId: GUEST_USER_ID,
        });

        if (!conversation) {
            return NextResponse.json({ error: 'Conversation not found' }, { status: 404 });
        }

        // Also delete all messages in this conversation
        await Message.deleteMany({ conversationId: id });

        return NextResponse.json({ message: 'Conversation deleted successfully' });
    } catch (error: any) {
        console.error('Delete conversation error:', error);
        return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
    }
}
