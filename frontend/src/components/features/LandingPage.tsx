import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Link } from "@tanstack/react-router";
import { Braces, Bug, Code, Cpu, FileText } from "lucide-react";

const teamMembers = [
	{ name: "Rupak", role: "রুপোকোনুজোন", emoji: "🧙‍♂️" },
	{ name: "Minhaz", role: "নেতা", emoji: "🎯" },
	{ name: "Saddat", role: "পাতি নেতা", emoji: "⚔️" },
];

export function LandingPage() {
	return (
		<div className="min-h-screen bg-gray-950 text-white overflow-hidden font-cabinet">
			{/* Cyberpunk Grid Background */}
			<div className="fixed inset-0 pointer-events-none">
				<div className="absolute inset-0 bg-[linear-gradient(rgba(0,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(0,255,255,0.03)_1px,transparent_1px)] bg-[size:50px_50px]" />
				<div className="absolute inset-0 bg-gradient-to-b from-transparent via-purple-900/10 to-cyan-900/20" />
			</div>

			{/* Floating Neon Orbs */}
			<div className="fixed inset-0 pointer-events-none overflow-hidden">
				<div className="absolute top-20 left-10 w-72 h-72 bg-cyan-500/20 rounded-full blur-[100px] animate-pulse" />
				<div className="absolute top-40 right-20 w-96 h-96 bg-purple-500/20 rounded-full blur-[120px] animate-pulse delay-700" />
				<div className="absolute bottom-20 left-1/3 w-80 h-80 bg-pink-500/15 rounded-full blur-[100px] animate-pulse delay-1000" />
			</div>

			{/* Header */}
			<header className="relative z-10">
				<nav className="flex items-center justify-between px-6 py-6 md:px-12 lg:px-20">
					<div className="flex items-center gap-3">
						<img
							src="/HFB_IB2.svg"
							alt="Hugs for Bugs Logo"
							className="absolute animate-pulse w-12 h-12 drop-shadow-[0_0_10px_rgba(0,255,255,0.8)]"
						/>
					</div>
					<div className="px-4 py-2 border border-cyan-500/50 rounded-lg bg-cyan-500/10 backdrop-blur-sm">
						<span className="text-cyan-400 font-mono text-sm">
							HACKATHON_2026
						</span>
					</div>
				</nav>
			</header>

			{/* Hero Section */}
			<main className="relative z-10">
				<section className="flex flex-col items-center justify-center px-6 py-16 md:py-24 text-center">
					{/* Glitch Title */}
					<div className="relative mb-6">
						<div className="absolute -inset-2 bg-gradient-to-r from-cyan-500 via-purple-500 to-pink-500 rounded-lg blur-xl opacity-30 animate-pulse" />
						<div className="relative px-6 py-3 bg-gray-900/80 border border-cyan-500/30 rounded-lg backdrop-blur-sm">
							<span className="font-mono text-cyan-400 text-sm md:text-base tracking-widest">
								{">"} TEAM_INITIALIZED{" "}
								<span className="animate-pulse">█</span>
							</span>
						</div>
					</div>

					<h1 className="text-6xl md:text-8xl lg:text-9xl font-black mb-6 leading-none font-clash">
						<span className="block text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-purple-400 to-pink-500 drop-shadow-[0_0_30px_rgba(0,255,255,0.3)]">
							HUGS
						</span>
						<span className="block text-transparent bg-clip-text bg-gradient-to-r from-pink-500 via-purple-400 to-cyan-400 drop-shadow-[0_0_30px_rgba(255,0,255,0.3)]">
							FOR BUGS
						</span>
					</h1>

					<p className="max-w-2xl text-xl md:text-2xl text-gray-400 mb-4 font-light">
						<span className="text-cyan-400">//</span> Where
						debugging meets{" "}
						<span className="text-pink-400 font-bold">
							compassion
						</span>
					</p>

					<p className="max-w-xl text-lg text-gray-500 mb-10 font-mono">
						{"<"}Every bug deserves a hug before it's squashed{"/>"}
					</p>

					<div className="flex flex-col sm:flex-row gap-4 mb-16">
						<Link to="/app">
							<Button
								size="lg"
								className="relative group px-8 py-6 text-lg font-bold bg-gradient-to-r from-cyan-500 to-purple-500 hover:from-cyan-400 hover:to-purple-400 text-gray-950 rounded-lg shadow-[0_0_30px_rgba(0,255,255,0.3)] hover:shadow-[0_0_50px_rgba(0,255,255,0.5)] transition-all duration-300">
								<FileText className="w-5 h-5 mr-2" />
								Start Document Prep. App
								<div className="absolute inset-0 rounded-lg bg-gradient-to-r from-cyan-400 to-purple-400 opacity-0 group-hover:opacity-20 transition-opacity" />
							</Button>
						</Link>
					</div>

					{/* Stats Bar */}
					<div className="flex flex-wrap justify-center gap-8 px-8 py-4 bg-gray-900/50 border border-cyan-500/20 rounded-xl backdrop-blur-sm font-space">
						<div className="text-center">
							<div className="text-3xl font-black text-cyan-400">
								∞
							</div>
							<div className="text-xs text-gray-500 font-mono uppercase tracking-wider">
								Bugs Hugged
							</div>
						</div>
						<div className="text-center">
							<div className="text-3xl font-black text-purple-400">
								42
							</div>
							<div className="text-xs text-gray-500 font-mono uppercase tracking-wider">
								Hours Hacking
							</div>
						</div>
						<div className="text-center">
							<div className="text-3xl font-black text-pink-400">
								☕×∞
							</div>
							<div className="text-xs text-gray-500 font-mono uppercase tracking-wider">
								Coffee Consumed
							</div>
						</div>
					</div>
				</section>

				{/* Team Section */}
				<section className="px-6 py-16 md:px-12 lg:px-20">
					<div className="max-w-5xl mx-auto">
						<div className="text-center mb-12">
							<h2 className="text-4xl md:text-5xl font-black mb-4">
								<span className="text-transparent bg-clip-text bg-gradient-to-r from-pink-500 to-cyan-400">
									{"{"} THE SQUAD {"}"}
								</span>
							</h2>
							<p className="text-gray-500 font-mono">
								console.log(
								<span className="text-cyan-400">
									"Meet the bug huggers"
								</span>
								);
							</p>
						</div>

						<div className="grid md:grid-cols-3 gap-6">
							{teamMembers.map((member, index) => (
								<Card
									key={member.name}
									className="group relative bg-gray-900/70 border-2 border-gray-800 hover:border-cyan-500/50 backdrop-blur-sm transition-all duration-500 overflow-hidden">
									{/* Hover glow effect */}
									<div className="absolute inset-0 bg-gradient-to-br from-cyan-500/0 via-purple-500/0 to-pink-500/0 group-hover:from-cyan-500/10 group-hover:via-purple-500/10 group-hover:to-pink-500/10 transition-all duration-500" />

									{/* Top accent line */}
									<div
										className={`absolute top-0 left-0 right-0 h-1 bg-gradient-to-r ${
											index === 0
												? "from-cyan-500 to-purple-500"
												: index === 1
													? "from-purple-500 to-pink-500"
													: "from-pink-500 to-cyan-500"
										}`}
									/>

									<CardContent className="relative p-8 text-center">
										<div className="text-6xl mb-4 group-hover:scale-110 transition-transform duration-300">
											{member.emoji}
										</div>
										<h3
											className={`text-2xl font-black mb-2 ${
												index === 0
													? "text-cyan-400"
													: index === 1
														? "text-purple-400"
														: "text-pink-400"
											}`}>
											{member.name}
										</h3>
										<p className="text-gray-500 font-mono text-sm">
											{"< "}
											{member.role}
											{" />"}
										</p>

										{/* Terminal-style decoration */}
										<div className="mt-4 pt-4 border-t border-gray-800">
											<code className="text-xs text-gray-600">
												status:{" "}
												<span className="text-green-400">
													ONLINE
												</span>
											</code>
										</div>
									</CardContent>
								</Card>
							))}
						</div>
					</div>
				</section>

				{/* Mission Statement */}
				<section className="px-6 py-16 md:px-12 lg:px-20">
					<div className="max-w-4xl mx-auto">
						<Card className="relative bg-gray-900/50 border border-purple-500/30 backdrop-blur-sm overflow-hidden">
							{/* Animated border */}
							<div className="absolute inset-0 bg-gradient-to-r from-cyan-500 via-purple-500 to-pink-500 opacity-20" />
							<div className="absolute inset-[1px] bg-gray-900/95 rounded-lg" />

							<CardContent className="relative p-8 md:p-12">
								<div className="flex items-start gap-4">
									<div className="hidden md:flex flex-col items-center text-gray-700 font-mono text-sm">
										<span>01</span>
										<span>02</span>
										<span>03</span>
										<span>04</span>
										<span>05</span>
									</div>
									<div>
										<div className="flex items-center gap-3 mb-4">
											<Braces className="w-8 h-8 text-cyan-400" />
											<h3 className="text-2xl font-black text-gray-200">
												OUR_MISSION
											</h3>
										</div>
										<p className="text-lg text-gray-400 leading-relaxed mb-4">
											<span className="text-purple-400 font-mono">
												/*
											</span>
										</p>
										<p className="text-xl text-gray-300 leading-relaxed pl-4 border-l-2 border-purple-500/50">
											In a world of ruthless debugging, we
											choose
											<span className="text-pink-400 font-bold">
												{" "}
												compassion
											</span>
											. Every bug tells a story, every
											error is a lesson, and every glitch
											deserves a
											<span className="text-cyan-400 font-bold">
												{" "}
												hug{" "}
											</span>
											before being fixed.
										</p>
										<p className="text-lg text-gray-400 leading-relaxed mt-4">
											<span className="text-purple-400 font-mono">
												*/
											</span>
										</p>
									</div>
								</div>
							</CardContent>
						</Card>
					</div>
				</section>

				{/* Tech Stack Pills */}
				<section className="px-6 py-8 mb-8">
					<div className="flex flex-wrap justify-center gap-3 max-w-4xl mx-auto">
						{[
							"React",
							"TypeScript",
							"FastAPI",
							"Tailwind",
							"Python",
							"☕ Coffee",
						].map((tech) => (
							<div
								key={tech}
								className="px-4 py-2 bg-gray-900/50 border border-gray-800 rounded-full font-mono text-sm text-gray-400 hover:border-cyan-500/50 hover:text-cyan-400 transition-all duration-300">
								{tech}
							</div>
						))}
					</div>
				</section>

				{/* Footer */}
				<footer className="relative z-10 px-6 py-8 border-t border-gray-800">
					<div className="max-w-5xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
						<div className="flex items-center gap-2">
							<Bug className="w-5 h-5 text-cyan-400" />
							<span className="font-mono text-gray-500">
								./hugs_for_bugs
							</span>
						</div>
						<div className="flex items-center gap-2 text-gray-600 font-mono text-sm">
							<Code className="w-4 h-4" />
							<span>HACKATHON_2026</span>
							<span className="text-pink-500">♥</span>
							<Cpu className="w-4 h-4" />
						</div>
						<p className="text-gray-600 font-mono text-sm">
							Made with <span className="text-pink-500">💜</span>{" "}
							and <span className="text-cyan-400">bugs</span>
						</p>
					</div>
				</footer>
			</main>
		</div>
	);
}
