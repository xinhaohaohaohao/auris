declare module "howler" {
  type SpriteDefinition = Record<string, [number, number, boolean?]>;

  type HowlOptions = {
    src: string[];
    html5?: boolean;
    preload?: boolean | "metadata";
    rate?: number;
    sprite?: SpriteDefinition;
    onplay?: () => void;
    onpause?: () => void;
    onstop?: () => void;
    onend?: () => void;
    onload?: () => void;
    onloaderror?: (id?: number, error?: unknown) => void;
    onplayerror?: (id?: number, error?: unknown) => void;
  };

  export class Howl {
    constructor(options: HowlOptions);
    play(): number;
    pause(id?: number): this;
    stop(id?: number): this;
    unload(): void;
    seek(position?: number, id?: number): number | this;
    duration(id?: number): number;
    rate(rate?: number, id?: number): number | this;
  }
}
