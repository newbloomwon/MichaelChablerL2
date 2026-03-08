import { useState, FC, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../lib/api';
import { Lock, Mail, Loader2, Sparkles } from 'lucide-react';

export const LoginPage: FC = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);

        try {
            const response = await api.post('/api/auth/login', {
                username: email,
                password: password
            });
            if (response.data.success) {
                login(response.data.data.access_token, response.data.data.user);
                navigate('/');
            } else {
                setError('Login failed');
            }
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to login. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen w-full flex items-center justify-center bg-transparent p-4 relative overflow-hidden">
            <div className="w-full max-w-md glass-panel p-10 z-10 relative">
                <div className="tape-strip -top-3 left-1/4"></div>
                <div className="tape-strip -top-3 right-1/4 rotate-[2deg]"></div>

                <div className="flex flex-col items-center mb-10">
                    <h1 className="text-6xl font-marker text-ink -rotate-2 mb-2">Punkt</h1>
                    <p className="text-ink/60 font-typewriter text-sm uppercase tracking-widest">Enterprise Log Intelligence</p>
                </div>

                {error && (
                    <div className="mb-6 p-4 bg-error/10 border-2 border-error text-error text-xs font-typewriter font-bold uppercase tracking-wider">
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-6">
                    <div className="space-y-2">
                        <label className="text-xs font-typewriter uppercase tracking-wider text-ink/70 ml-1">Email Address</label>
                        <div className="relative">
                            <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-ink/40" size={16} />
                            <input
                                type="email"
                                required
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="input-field pl-12"
                                placeholder="name@company.com"
                            />
                        </div>
                    </div>

                    <div className="space-y-2">
                        <label className="text-xs font-typewriter uppercase tracking-wider text-ink/70 ml-1">Password</label>
                        <div className="relative">
                            <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-ink/40" size={16} />
                            <input
                                type="password"
                                required
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="input-field pl-12"
                                placeholder="••••••••"
                            />
                        </div>
                    </div>

                    <div className="flex items-center justify-between px-1">
                        <label className="flex items-center gap-2 cursor-pointer group/check">
                            <input type="checkbox" className="w-4 h-4 border-2 border-ink bg-white text-ink focus:ring-accent" />
                            <span className="text-xs font-typewriter text-ink/60 uppercase tracking-wider group-hover/check:text-ink">Remember me</span>
                        </label>
                        <a href="#" className="text-xs font-typewriter font-bold text-ink bg-accent/30 px-2 py-1 hover:bg-accent uppercase tracking-wider">Forgot?</a>
                    </div>

                    <button
                        type="submit"
                        disabled={isLoading}
                        className="btn-primary w-full py-4 flex items-center justify-center gap-3 uppercase tracking-[0.3em] text-xs font-black italic"
                    >
                        {isLoading ? (
                            <Loader2 className="animate-spin" size={20} />
                        ) : (
                            <>
                                <span>Authenticate</span>
                                <Sparkles size={18} />
                            </>
                        )}
                    </button>
                </form>

                <p className="mt-10 text-center text-xs font-typewriter text-ink/40 uppercase tracking-widest">
                    Punkt Engine v2.0 // Sentinel v1.4
                </p>
            </div>
        </div>
    );
};
