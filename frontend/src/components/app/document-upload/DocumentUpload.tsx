import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Upload } from "lucide-react";
import React from "react";

// --- Sub-components ---

function Header({
	children,
	className,
}: {
	children: React.ReactNode;
	className?: string;
}) {
	return (
		<CardHeader
			className={`text-center border-b border-gray-800 ${className}`}>
			<CardTitle className="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-purple-400 font-clash">
				{children}
			</CardTitle>
		</CardHeader>
	);
}

function Zone() {
	return (
		<div className="space-y-6">
			<div className="w-24 h-24 mx-auto rounded-full bg-gradient-to-br from-cyan-500/20 to-purple-500/20 flex items-center justify-center border border-cyan-500/30">
				<Upload className="w-12 h-12 text-cyan-400" />
			</div>

			<div className="space-y-2">
				<p className="text-xl text-gray-300">Target Zone Acquired</p>
				<p className="text-gray-500 font-mono text-sm font-space">
					// TODO: Initialize drag-and-drop protocols
				</p>
			</div>
		</div>
	);
}

function Status({ status = "AWAITING_INPUT" }: { status?: string }) {
	return (
		<div className="pt-4 border-t border-gray-800">
			<code className="text-xs text-gray-600 font-mono font-space">
				status: <span className="text-yellow-400">{status}</span>
			</code>
		</div>
	);
}

// --- Root Component ---

interface DocumentUploadProps {
	children: React.ReactNode;
	className?: string;
}

export function DocumentUpload({ children, className }: DocumentUploadProps) {
	return (
		<Card
			className={`max-w-2xl w-full bg-gray-900/70 border-2 border-cyan-500/30 backdrop-blur-sm ${className}`}>
			{children}
		</Card>
	);
}

// --- Attach Sub-components ---
DocumentUpload.Header = Header;
DocumentUpload.Content = CardContent; // Re-exporting CardContent for convenience or we can wrap it
DocumentUpload.Zone = Zone;
DocumentUpload.Status = Status;
