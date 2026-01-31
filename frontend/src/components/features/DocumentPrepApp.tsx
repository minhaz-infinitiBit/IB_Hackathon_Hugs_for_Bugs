import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Link } from "@tanstack/react-router";
import { ArrowLeft, FileText } from "lucide-react";

export function DocumentPrepApp() {
	return (
		<div className="min-h-screen bg-gray-950 text-white font-cabinet">
			{/* Background Grid */}
			<div className="fixed inset-0 pointer-events-none">
				<div className="absolute inset-0 bg-[linear-gradient(rgba(0,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(0,255,255,0.03)_1px,transparent_1px)] bg-[size:50px_50px]" />
				<div className="absolute inset-0 bg-gradient-to-b from-transparent via-purple-900/10 to-cyan-900/20" />
			</div>

			{/* Header */}
			<header className="relative z-10 border-b border-gray-800">
				<nav className="flex items-center justify-between px-6 py-4 md:px-12 lg:px-20">
					<div className="flex items-center gap-4">
						<Link to="/">
							<Button
								variant="ghost"
								size="sm"
								className="text-gray-400 hover:text-cyan-400">
								<ArrowLeft className="w-4 h-4 mr-2" />
								Back to Home
							</Button>
						</Link>
					</div>
					<div className="flex items-center gap-2">
						<FileText className="w-5 h-5 text-cyan-400" />
						<span className="font-mono text-cyan-400">
							Document Prep App
						</span>
					</div>
				</nav>
			</header>

			{/* Main Content */}
			<main className="relative z-10 flex items-center justify-center min-h-[calc(100vh-80px)] px-6">
				<Card className="max-w-2xl w-full bg-gray-900/70 border-2 border-cyan-500/30 backdrop-blur-sm">
					<CardHeader className="text-center border-b border-gray-800">
						<CardTitle className="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-purple-400 font-clash">
							📄 Document Prep App
						</CardTitle>
					</CardHeader>
					<CardContent className="p-8 text-center">
						<div className="space-y-6">
							<div className="w-24 h-24 mx-auto rounded-full bg-gradient-to-br from-cyan-500/20 to-purple-500/20 flex items-center justify-center border border-cyan-500/30">
								<FileText className="w-12 h-12 text-cyan-400" />
							</div>

							<div className="space-y-2">
								<p className="text-xl text-gray-300">
									Coming Soon...
								</p>
								<p className="text-gray-500 font-mono text-sm">
									// TODO: Build awesome document preparation
									features
								</p>
							</div>

							<div className="pt-4 border-t border-gray-800">
								<code className="text-xs text-gray-600 font-mono font-space">
									status:{" "}
									<span className="text-yellow-400">
										IN_DEVELOPMENT
									</span>
								</code>
							</div>
						</div>
					</CardContent>
				</Card>
			</main>
		</div>
	);
}
