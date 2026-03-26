"use client"
import React from "react";

const Button = ({ text, color, onClick }: { text: string, color: string, onClick?: () => void }) => {
    const colorMap: Record<string, string> = {
        blue: "bg-blue-500 hover:bg-blue-600",
        red: "bg-red-500 hover:bg-red-600",
        green: "bg-green-500 hover:bg-green-600",
        zinc: "bg-zinc-500 hover:bg-zinc-600",
    };

    const colorClasses = colorMap[color] || colorMap.blue;

    return (
        <button
            onClick={onClick}
            className={`${colorClasses} text-white font-semibold py-2 px-4 rounded transition duration-200`}
        >
            {text || "Button"}
        </button>
    );
};

export default Button;
