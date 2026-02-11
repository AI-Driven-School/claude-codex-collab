import {Composition} from 'remotion';
import {PromoVideo} from './PromoVideo';

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="PromoVideo"
        component={PromoVideo}
        durationInFrames={450}
        fps={30}
        width={1280}
        height={720}
      />
      <Composition
        id="PromoVideoSquare"
        component={PromoVideo}
        durationInFrames={450}
        fps={30}
        width={1080}
        height={1080}
      />
    </>
  );
};
