import { NextRequest, NextResponse } from 'next/server';
import connectDB from '@/lib/mongodb';
import Message from '@/models/Message';
import Conversation from '@/models/Conversation';

const GUEST_USER_ID = 'guest';

export async function PATCH(
    req: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id } = await params;
        const { content } = await req.json();

        await connectDB();

        // Verify ownership via conversation
        const message = await Message.findById(id);
        if (!message) {
            return NextResponse.json({ error: 'Message not found' }, { status: 404 });
        }

        const conversation = await Conversation.findOne({
            _id: message.conversationId,
            userId: GUEST_USER_ID,
        });

        if (!conversation) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 403 });
        }

        message.content = content;
        await message.save();

        return NextResponse.json(message);
    } catch (error: any) {
        console.error('Update message error:', error);
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

        // Verify ownership via conversation
        const message = await Message.findById(id);
        if (!message) {
            return NextResponse.json({ error: 'Message not found' }, { status: 404 });
        }

        const conversation = await Conversation.findOne({
            _id: message.conversationId,
            userId: GUEST_USER_ID,
        });

        if (!conversation) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 403 });
        }

        await Message.findByIdAndDelete(id);

        return NextResponse.json({ message: 'Message deleted successfully' });
    } catch (error: any) {
        console.error('Delete message error:', error);
        return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
    }
}
