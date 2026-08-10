import { PixelBackground } from "@/components/unlumen-ui/pixel";

export const PixelBackgroundGridDemo = () => {
  return (
    <div className="absolute m-12 border border-border/80 inset-0 grid grid-cols-3 overflow-hidden divide-x divide-border/80">
      <PixelBackground
        pattern="cursor"
        darkColors="#0d1b4b,#1a3a8f,#2563eb"
        lightColors="#bfdbfe,#93c5fd,#3b82f6"
        className="size-full flex flex-col"
      >
        <h1 className="text-4xl p-6 pb-1">
          Pixel <br /> Cursor
        </h1>
        <p className="text-sm text-muted-foreground p-6 pt-3">
          Animation starts from where the mouse enters.
        </p>
      </PixelBackground>

      <PixelBackground
        pattern="edges"
        darkColors="#2a2a2a,#3b3b3b,#525252"
        lightColors="#d4d4d4,#bdbdbd,#a3a3a3"
        className="size-full flex flex-col"
      >
        <h1 className="text-4xl p-6 pb-1">
          Pixel <br /> Edges
        </h1>
        <p className="text-sm text-muted-foreground p-6 pt-3">
          Pixels appear from all edges inward.
        </p>
      </PixelBackground>

      <PixelBackground
        pattern="random"
        darkColors="#606c38,#fefae0,#bc6c25"
        lightColors="#264653,#2a9d8f,#e9c46a,#f4a261"
        className="size-full flex flex-col"
      >
        <h1 className="text-4xl p-6 pb-1">
          Pixel <br /> Random
        </h1>
        <p className="text-sm text-muted-foreground p-6 pt-3">
          A Random pattern that combines distance and angle
        </p>
      </PixelBackground>
    </div>
  );
};
