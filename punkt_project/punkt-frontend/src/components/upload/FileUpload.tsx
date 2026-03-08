import { FC, useState, useRef } from 'react';
import { Upload, FileText, CheckCircle2, AlertCircle, Loader2, X } from 'lucide-react';
import api from '../../lib/api';
import { cn } from '../../lib/utils';

const CHUNK_SIZE = 1024 * 1024; // 1MB

interface FileUploadProps {
    onComplete?: (jobId: string) => void;
}

export const FileUpload: FC<FileUploadProps> = ({ onComplete }) => {
    const [file, setFile] = useState<File | null>(null);
    const [sourceName, setSourceName] = useState('');
    const [format, setFormat] = useState<'json' | 'nginx'>('json');
    const [uploading, setUploading] = useState(false);
    const [progress, setProgress] = useState(0);
    const [currentChunk, setCurrentChunk] = useState(0);
    const [totalChunks, setTotalChunks] = useState(0);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState(false);

    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const selectedFile = e.target.files?.[0];
        if (selectedFile) {
            setFile(selectedFile);
            if (!sourceName) {
                setSourceName(selectedFile.name);
            }
            setError(null);
            setSuccess(false);
        }
    };

    const uploadFile = async () => {
        if (!file || !sourceName) return;

        setUploading(true);
        setError(null);
        setProgress(0);

        const chunks = Math.ceil(file.size / CHUNK_SIZE);
        setTotalChunks(chunks);

        try {
            // 1. Initialize upload
            const initRes = await api.post('/api/ingest/file/init', {
                filename: file.name,
                source: sourceName,
                format: format,
                total_size: file.size,
                total_chunks: chunks
            });

            if (!initRes.data.success) {
                throw new Error(initRes.data.error?.message || 'Failed to initialize upload');
            }

            const { upload_id } = initRes.data.data;

            // 2. Upload chunks
            for (let i = 0; i < chunks; i++) {
                setCurrentChunk(i + 1);
                const start = i * CHUNK_SIZE;
                const end = Math.min(file.size, start + CHUNK_SIZE);
                const chunk = file.slice(start, end);

                const formData = new FormData();
                formData.append('chunk', chunk);
                formData.append('chunk_index', i.toString());
                formData.append('upload_id', upload_id);

                const chunkRes = await api.post('/api/ingest/file/chunk', formData, {
                    headers: { 'Content-Type': 'multipart/form-data' }
                });

                if (!chunkRes.data.success) {
                    throw new Error(chunkRes.data.error?.message || `Failed to upload chunk ${i + 1}`);
                }

                setProgress(Math.round(((i + 1) / chunks) * 100));
            }

            // 3. Complete upload
            const completeRes = await api.post('/api/ingest/file/complete', {
                upload_id: upload_id
            });

            if (!completeRes.data.success) {
                throw new Error(completeRes.data.error?.message || 'Failed to finalize upload');
            }

            setSuccess(true);
            if (onComplete) onComplete(completeRes.data.data.job_id);

            // Reset after success
            setTimeout(() => {
                setFile(null);
                setSourceName('');
                setSuccess(false);
                setProgress(0);
            }, 3000);

        } catch (err: any) {
            setError(err.response?.data?.error?.message || err.message || 'An error occurred during upload');
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="w-full max-w-2xl mx-auto bg-secondary p-8 rounded-3xl border border-gray-800 shadow-2xl">
            <div className="mb-8">
                <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                    <Upload className="text-primary" />
                    Ingest Log Data
                </h2>
                <p className="text-gray-400 mt-2">Upload large JSON or Nginx log files for processing.</p>
            </div>

            <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-gray-400 ml-1">Source Name</label>
                        <input
                            type="text"
                            value={sourceName}
                            onChange={(e) => setSourceName(e.target.value)}
                            placeholder="e.g. production-nginx"
                            className="w-full bg-gray-950 border border-gray-800 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
                            disabled={uploading}
                        />
                    </div>
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-gray-400 ml-1">Log Format</label>
                        <select
                            value={format}
                            onChange={(e) => setFormat(e.target.value as 'json' | 'nginx')}
                            className="w-full bg-gray-950 border border-gray-800 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all appearance-none"
                            disabled={uploading}
                        >
                            <option value="json">JSON / NDJSON</option>
                            <option value="nginx">Nginx Combined</option>
                        </select>
                    </div>
                </div>

                {!file ? (
                    <div
                        onClick={() => fileInputRef.current?.click()}
                        className="border-2 border-dashed border-gray-800 rounded-2xl p-12 flex flex-col items-center justify-center cursor-pointer hover:border-primary/50 hover:bg-primary/5 transition-all group"
                    >
                        <div className="p-4 rounded-full bg-gray-900 mb-4 group-hover:scale-110 transition-transform">
                            <FileText className="text-gray-500 group-hover:text-primary" size={32} />
                        </div>
                        <p className="text-lg font-medium text-white">Click to select a file</p>
                        <p className="text-sm text-gray-500 mt-1">Maximum 500MB supported for chunked upload</p>
                        <input
                            ref={fileInputRef}
                            type="file"
                            className="hidden"
                            onChange={handleFileSelect}
                            accept=".json,.log,.txt,.ndjson"
                        />
                    </div>
                ) : (
                    <div className="bg-gray-950 border border-gray-800 rounded-2xl p-6 flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <div className="p-3 rounded-xl bg-primary/10 text-primary">
                                <FileText size={24} />
                            </div>
                            <div>
                                <p className="font-medium text-white max-w-[200px] truncate">{file.name}</p>
                                <p className="text-xs text-gray-500">{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
                            </div>
                        </div>
                        {!uploading && (
                            <button
                                onClick={() => setFile(null)}
                                className="p-2 text-gray-500 hover:text-error transition-colors"
                            >
                                <X size={20} />
                            </button>
                        )}
                    </div>
                )}

                {uploading && (
                    <div className="space-y-3">
                        <div className="flex justify-between text-sm">
                            <span className="text-gray-400">Uploading chunks...</span>
                            <span className="text-white font-medium">{progress}%</span>
                        </div>
                        <div className="w-full h-2 bg-gray-900 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-primary transition-all duration-300 shadow-[0_0_10px_rgba(139,92,246,0.5)]"
                                style={{ width: `${progress}%` }}
                            />
                        </div>
                        <p className="text-xs text-gray-500 text-center uppercase tracking-widest">
                            Chunk {currentChunk} of {totalChunks}
                        </p>
                    </div>
                )}

                {error && (
                    <div className="bg-error/10 border border-error/20 rounded-xl p-4 flex items-center gap-3 text-error">
                        <AlertCircle size={20} />
                        <p className="text-sm">{error}</p>
                    </div>
                )}

                {success && (
                    <div className="bg-success/10 border border-success/20 rounded-xl p-4 flex items-center gap-3 text-success">
                        <CheckCircle2 size={20} />
                        <p className="text-sm font-medium">Upload successful! Processing started.</p>
                    </div>
                )}

                <button
                    onClick={uploadFile}
                    disabled={!file || !sourceName || uploading || success}
                    className={cn(
                        "w-full py-4 rounded-xl font-bold text-lg transition-all flex items-center justify-center gap-3",
                        file && sourceName && !uploading && !success
                            ? "bg-primary text-white shadow-lg shadow-primary/20 hover:scale-[1.02]"
                            : "bg-gray-800 text-gray-500 cursor-not-allowed"
                    )}
                >
                    {uploading ? (
                        <>
                            <Loader2 className="animate-spin" />
                            Processing Chunks...
                        </>
                    ) : success ? (
                        <>
                            <CheckCircle2 />
                            Complete
                        </>
                    ) : (
                        <>
                            <Upload size={20} />
                            Start Ingestion
                        </>
                    )}
                </button>
            </div>
        </div>
    );
};
