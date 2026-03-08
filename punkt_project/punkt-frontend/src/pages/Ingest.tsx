import { FC } from 'react';
import { FileUpload } from '../components/upload/FileUpload';
import { History, ShieldAlert } from 'lucide-react';

export const IngestPage: FC = () => {
    return (
        <div className="space-y-8 animate-in fade-in transition-all duration-500">
            <div>
                <h1 className="text-3xl font-bold tracking-tight text-white">Data Ingestion</h1>
                <p className="text-gray-400 mt-1">Upload and process log data into the Punkt platform.</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2">
                    <FileUpload />
                </div>

                <div className="space-y-6">
                    <div className="bg-secondary p-6 rounded-3xl border border-gray-800 shadow-xl">
                        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                            <ShieldAlert className="text-accent" size={20} />
                            Upload Policy
                        </h3>
                        <ul className="space-y-3 text-sm text-gray-400">
                            <li className="flex items-start gap-2">
                                <div className="w-1.5 h-1.5 rounded-full bg-accent mt-1.5 shrink-0" />
                                Max file size: 500MB
                            </li>
                            <li className="flex items-start gap-2">
                                <div className="w-1.5 h-1.5 rounded-full bg-accent mt-1.5 shrink-0" />
                                Supported formats: JSON, NDJSON, Nginx Combined Log
                            </li>
                            <li className="flex items-start gap-2">
                                <div className="w-1.5 h-1.5 rounded-full bg-accent mt-1.5 shrink-0" />
                                Chunked upload ensures reliability for large files
                            </li>
                        </ul>
                    </div>

                    <div className="bg-secondary p-6 rounded-3xl border border-gray-800 shadow-xl">
                        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                            <History className="text-primary" size={20} />
                            Recent Uploads
                        </h3>
                        <div className="flex flex-col items-center justify-center py-8 text-gray-500 italic text-sm text-center">
                            <p>No recent uploads found.</p>
                            <p className="mt-1">Active jobs will appear here.</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
