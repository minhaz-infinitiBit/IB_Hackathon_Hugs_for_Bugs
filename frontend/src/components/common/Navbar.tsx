import { Button } from "@/components/ui/button";
import { Link } from "@tanstack/react-router";
import { ArrowLeft, FileText } from "lucide-react";

export function Navbar() {
	return (
		<header className="relative z-10 border-b border-gray-800 bg-gray-950/50 backdrop-blur-md">
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
					<span className="font-mono text-cyan-400 font-space tracking-wide">
						Document Prep App
					</span>
				</div>
			</nav>
		</header>
	);
}
