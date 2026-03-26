export default function Footer() {
    return (
        <footer className="bg-white border-t border-slate-200 py-10">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
                    <div className="flex items-center space-x-2">
                        <div className="w-8 h-8 bg-indigo-100 rounded-lg flex items-center justify-center">
                            <span className="text-indigo-600 font-bold">S</span>
                        </div>
                        <span className="text-slate-900 font-semibold tracking-tight">SheaBot</span>
                    </div>

                    <div className="flex space-x-6 text-sm text-slate-500">
                        <a href="#" className="hover:text-indigo-600 transition-colors">Privacy Policy</a>
                        <a href="#" className="hover:text-indigo-600 transition-colors">Terms of Service</a>
                        <a href="#" className="hover:text-indigo-600 transition-colors">Contact Support</a>
                    </div>

                    <div className="text-sm text-slate-400">
                        &copy; {new Date().getFullYear()} SheaBot AI. All rights reserved.
                    </div>
                </div>
            </div>
        </footer>
    );
}
