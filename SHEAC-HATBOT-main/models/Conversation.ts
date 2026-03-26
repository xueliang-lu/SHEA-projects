import mongoose, { Schema, Model } from 'mongoose';
import { IConversation } from '@/types';

const ConversationSchema = new Schema<IConversation>(
    {
        userId: {
            type: String,
            required: [true, 'User ID is required'],
            index: true,
        },
        title: {
            type: String,
            required: true,
            default: 'New Conversation',
            maxlength: [200, 'Title cannot exceed 200 characters'],
        },
        lastMessageAt: {
            type: Date,
            default: Date.now,
            index: true,
        },
    },
    {
        timestamps: true,
    }
);

// Index for efficient querying of user's conversations sorted by last message
ConversationSchema.index({ userId: 1, lastMessageAt: -1 });

const Conversation: Model<IConversation> =
    mongoose.models.Conversation || mongoose.model<IConversation>('Conversation', ConversationSchema);

export default Conversation;
