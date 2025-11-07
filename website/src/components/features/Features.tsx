'use client';
import { useEffect, useRef, useState } from 'react';

export default function Features() {
	const canvasRef = useRef<HTMLCanvasElement>(null);
	const sectionRef = useRef<HTMLDivElement>(null);
	const [loaded, setLoaded] = useState(false);
	const [loadProgress, setLoadProgress] = useState(0);

	useEffect(() => {
		let ctx: CanvasRenderingContext2D | null = null;
		let currentFrame = 1;
		const frameCount = 1494;
		const images: { [key: number]: HTMLImageElement } = {};
		const MAX_CACHED_FRAMES = 100;
		let frameCache: number[] = [];
		let animationFrame: number;
		let isMounted = true;

		const createFallbackFrame = (frameIndex: number): HTMLImageElement => {
			const fallbackCanvas = document.createElement('canvas');
			fallbackCanvas.width = 1920;
			fallbackCanvas.height = 1080;
			const fallbackCtx = fallbackCanvas.getContext('2d')!;

			const hue = (frameIndex / frameCount) * 360;
			fallbackCtx.fillStyle = `hsl(${hue}, 50%, 10%)`;
			fallbackCtx.fillRect(0, 0, fallbackCanvas.width, fallbackCanvas.height);

			fallbackCtx.fillStyle = '#fff';
			fallbackCtx.font = '48px Arial';
			fallbackCtx.textAlign = 'center';
			fallbackCtx.fillText(
				`Frame ${frameIndex}`,
				fallbackCanvas.width / 2,
				fallbackCanvas.height / 2
			);

			const img = new Image();
			img.src = fallbackCanvas.toDataURL();
			return img;
		};

		const loadFrame = (frameIndex: number): Promise<void> => {
			return new Promise((resolve) => {
				if (images[frameIndex]) {
					resolve();
					return;
				}

				const img = new Image();
				const loadTimeout = setTimeout(() => {
					console.warn(`Frame ${frameIndex} load timeout`);
					images[frameIndex] = createFallbackFrame(frameIndex);
					resolve();
				}, 5000);

				img.onload = () => {
					clearTimeout(loadTimeout);
					images[frameIndex] = img;
					resolve();
				};

				img.onerror = () => {
					clearTimeout(loadTimeout);
					console.error(`Failed to load frame ${frameIndex}`);
					images[frameIndex] = createFallbackFrame(frameIndex);
					resolve();
				};

				img.src = `/images/slides/frames/frame_${String(frameIndex).padStart(
					4,
					'0'
				)}.png`;
			});
		};

		const preloadFrames = async (
			start: number,
			count: number
		): Promise<void> => {
			const promises = [];
			const end = Math.min(start + count - 1, frameCount);
			let loaded = 0;

			for (let i = start; i <= end; i++) {
				promises.push(
					loadFrame(i).then(() => {
						if (!isMounted) return;
						loaded++;
						setLoadProgress((loaded / count) * 100);
					})
				);
			}

			await Promise.all(promises);
		};

		const manageCache = (currentFrame: number) => {
			// Keep current frame and nearby frames
			const keepFrames = new Set<number>();
			const buffer = 20;

			for (
				let i = Math.max(1, currentFrame - buffer);
				i <= Math.min(frameCount, currentFrame + buffer);
				i++
			) {
				keepFrames.add(i);
			}

			// Remove frames outside buffer range
			frameCache = frameCache.filter((frame) => keepFrames.has(frame));

			// Add current frame to cache
			if (!frameCache.includes(currentFrame)) {
				frameCache.push(currentFrame);
			}

			// If cache is too large, remove oldest
			while (frameCache.length > MAX_CACHED_FRAMES) {
				const oldestFrame = frameCache.shift();
				if (
					oldestFrame &&
					images[oldestFrame] &&
					!keepFrames.has(oldestFrame)
				) {
					delete images[oldestFrame];
				}
			}
		};

		const drawFallback = (frameIndex: number) => {
			if (!ctx) return;

			ctx.fillStyle = '#222';
			ctx.fillRect(0, 0, ctx.canvas.width, ctx.canvas.height);

			ctx.fillStyle = '#666';
			ctx.font = '18px Arial';
			ctx.textAlign = 'center';
			ctx.fillText(
				`Loading frame ${frameIndex}/${frameCount}`,
				ctx.canvas.width / 2,
				ctx.canvas.height / 2
			);

			// Progress bar
			const progressWidth = ctx.canvas.width * 0.6;
			const progressHeight = 4;
			const progressX = (ctx.canvas.width - progressWidth) / 2;
			const progressY = ctx.canvas.height / 2 + 30;

			ctx.fillStyle = '#333';
			ctx.fillRect(progressX, progressY, progressWidth, progressHeight);

			const loadedProgress = frameIndex / frameCount;
			ctx.fillStyle = '#fff';
			ctx.fillRect(
				progressX,
				progressY,
				progressWidth * loadedProgress,
				progressHeight
			);
		};

		const draw = () => {
			if (!ctx || !isMounted) return;

			const frameIndex = Math.round(currentFrame);

			animationFrame = requestAnimationFrame(() => {
				if (!ctx) return;
				ctx.fillStyle = '#111';
				ctx.fillRect(0, 0, ctx.canvas.width, ctx.canvas.height);

				const img = images[frameIndex];
				if (img && img.complete && ctx) {
					ctx.drawImage(img, 0, 0, ctx.canvas.width, ctx.canvas.height);
				} else {
					drawFallback(frameIndex);

					// Load this frame if not loaded
					if (!img) {
						loadFrame(frameIndex).then(() => {
							if (isMounted && Math.round(currentFrame) === frameIndex) {
								draw();
							}
						});
					}
				}

				manageCache(frameIndex);
			});
		};

		const run = async () => {
			if (!isMounted) return;

			const { gsap } = await import('gsap');
			const { ScrollTrigger } = await import('gsap/ScrollTrigger');
			gsap.registerPlugin(ScrollTrigger);

			const canvas = canvasRef.current;
			const section = sectionRef.current;

			if (!canvas || !section) return;

			ctx = canvas.getContext('2d');
			if (!ctx) return;

			// Set canvas size
			const setCanvasSize = () => {
				canvas.width = window.innerWidth;
				canvas.height = window.innerHeight;
				if (isMounted) {
					draw();
				}
			};

			setCanvasSize();

			// Preload initial frames
			await preloadFrames(1, 30);
			setLoaded(true);

			// Predictive loading function
			const loadFramesAround = (centerFrame: number, radius: number = 15) => {
				const start = Math.max(1, centerFrame - radius);
				const end = Math.min(frameCount, centerFrame + radius);
				preloadFrames(start, end - start + 1);
			};

			// Initial load around first frame
			loadFramesAround(1);

			// Scroll animation
			gsap.to(
				{ frame: 1 },
				{
					frame: frameCount,
					snap: 'frame',
					ease: 'none',
					scrollTrigger: {
						trigger: section,
						start: 'top top',
						end: `+=${frameCount * 10}`,
						scrub: true,
						pin: true,
						onUpdate: (self) => {
							if (!isMounted) return;
							currentFrame = self.progress * (frameCount - 1) + 1;

							// Load frames around current position
							loadFramesAround(Math.round(currentFrame));

							draw();
						},
						onEnter: () => {
							// Preload more frames when user starts scrolling
							loadFramesAround(1, 50);
						},
					},
				}
			);

			// Initial draw
			draw();

			const handleResize = () => {
				if (isMounted) {
					setCanvasSize();
				}
			};

			window.addEventListener('resize', handleResize);

			return () => {
				window.removeEventListener('resize', handleResize);
				ScrollTrigger.getAll().forEach((trigger) => trigger.kill());
				if (animationFrame) {
					cancelAnimationFrame(animationFrame);
				}
			};
		};

		run();

		return () => {
			isMounted = false;
			if (animationFrame) {
				cancelAnimationFrame(animationFrame);
			}
		};
	}, []);

	return (
		<section ref={sectionRef} className="relative w-full min-h-screen bg-black">
			<canvas ref={canvasRef} className="scroll-canvas w-full h-full" />
			{!loaded && (
				<div className="absolute inset-0 flex items-center justify-center bg-black">
					<div className="text-center text-white">
						<div className="text-xl mb-4">Loading animation...</div>
						<div className="w-64 h-2 bg-gray-700 rounded-full overflow-hidden">
							<div
								className="h-full bg-white transition-all duration-300"
								style={{ width: `${loadProgress}%` }}
							/>
						</div>
						<div className="text-sm mt-2">{Math.round(loadProgress)}%</div>
					</div>
				</div>
			)}
		</section>
	);
}
