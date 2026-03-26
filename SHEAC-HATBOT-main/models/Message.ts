import mongoose, { Schema, Model } from 'mongoose';
import { IMessage } from '@/types';

const MessageSchema = new Schema<IMessage>(
    {
        conversationId: {
            type: String,
            required: [true, 'Conversation ID is required'],
            index: true,
        },
        role: {
            type: String,
            required: true,
            enum: ['user', 'assistant'],
        },
        content: {
            type: String,
            required: [true, 'Message content is required'],
            maxlength: [10000, 'Message cannot exceed 10000 characters'],
        },
        aiProvider: {
            type: String,
            enum: ['openai', 'gemini'],
        },
    },
    {
        timestamps: true,
    }
);

// Index for efficient querying of messages in a conversation
MessageSchema.index({ conversationId: 1, createdAt: 1 });

const Message: Model<IMessage> =
    mongoose.models.Message || mongoose.model<IMessage>('Message', MessageSchema);

export default Message;
