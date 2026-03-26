import mongoose, { Schema, Model } from 'mongoose';
import { IFAQ } from '@/types';

const FAQSchema = new Schema<IFAQ>(
    {
        question: {
            type: String,
            required: [true, 'Question is required'],
            index: 'text',
            maxlength: [500, 'Question cannot exceed 500 characters'],
        },
        answer: {
            type: String,
            required: [true, 'Answer is required'],
            maxlength: [2000, 'Answer cannot exceed 2000 characters'],
        },
        embedding: {
            type: [Number],
        },
        category: {
            type: String,
            trim: true,
            index: true,
        },
    },
    {
        timestamps: true,
    }
);

// Text index for full-text search
FAQSchema.index({ question: 'text', answer: 'text' });

const FAQ: Model<IFAQ> = mongoose.models.FAQ || mongoose.model<IFAQ>('FAQ', FAQSchema);

export default FAQ;
