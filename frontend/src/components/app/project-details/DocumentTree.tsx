import {
	Accordion,
	AccordionContent,
	AccordionItem,
	AccordionTrigger,
} from "@/components/ui/accordion";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Folder } from "lucide-react";
import { DocumentTreeItem } from "./DocumentTreeItem";
import type { DocumentClassification } from "./types";

interface DocumentTreeProps {
	classifications: DocumentClassification[];
	isLoading?: boolean;
}

export function DocumentTree({
	classifications,
	isLoading,
}: DocumentTreeProps) {
	if (isLoading) {
		return (
			<div className="rounded-lg border border-gray-800 bg-gray-950/50 p-6">
				<p className="text-gray-400 font-mono text-center">
					Loading documents...
				</p>
			</div>
		);
	}

	if (classifications.length === 0) {
		return (
			<div className="rounded-lg border border-gray-800 bg-gray-950/50 p-6">
				<p className="text-gray-500 font-mono text-center">
					No documents found.
				</p>
			</div>
		);
	}

	return (
		<div className="rounded-lg border border-gray-800 bg-gray-950/50 backdrop-blur-sm">
			<div className="p-4 border-b border-gray-800">
				<h2 className="text-lg font-bold text-white font-clash">
					📁 Classified Documents
				</h2>
			</div>
			<ScrollArea className="h-[500px]">
				<Accordion
					type="multiple"
					className="p-4">
					{classifications.map((classification) => (
						<AccordionItem
							key={classification.id}
							value={classification.id}>
							<AccordionTrigger className="hover:no-underline">
								<div className="flex items-center gap-2">
									<Folder className="w-4 h-4 text-cyan-400" />
									<span className="text-white">
										{classification.name}
									</span>
									<span className="ml-2 px-2 py-0.5 rounded-full bg-gray-800 text-xs text-gray-400">
										{classification.count}
									</span>
								</div>
							</AccordionTrigger>
							<AccordionContent>
								<div className="space-y-2 pl-6">
									{classification.documents.map((doc) => (
										<DocumentTreeItem
											key={doc.id}
											document={doc}
										/>
									))}
								</div>
							</AccordionContent>
						</AccordionItem>
					))}
				</Accordion>
			</ScrollArea>
		</div>
	);
}
