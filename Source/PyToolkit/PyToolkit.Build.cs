// Some copyright should be here...

using UnrealBuildTool;

public class PyToolkit : ModuleRules
{
    public PyToolkit(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

        PublicIncludePaths.AddRange(
            new string[] {
				// ... add public include paths required here ...
			}
            );


        PrivateIncludePaths.AddRange(
            new string[] {
				// ... add other private include paths required here ...
			}
            );


        PublicDependencyModuleNames.AddRange(
            new string[]
            {
                "Core",
                "Sequencer",
                "SequencerWidgets",
                "MovieScene",
                "MovieSceneTracks",
				// ... add other public dependencies that you statically link with here ...
			}
            );


        PrivateDependencyModuleNames.AddRange(
            new string[]
            {
                "CoreUObject",
                "Engine",
                "Slate",
                "SlateCore",
                "SkeletonEditor",

                "LevelSequence",
                "SequencerScripting",
                "LevelSequenceEditor",
                "SequencerScriptingEditor",
                "Kismet",
                "PythonScriptPlugin",
                "MovieSceneCaptureDialog",
                "MovieSceneCapture",
                "SequencerScripting",
                "UnrealEd",
                //"Developer",
				// ... add private dependencies that you statically link with here ...	
			}
            );


        DynamicallyLoadedModuleNames.AddRange(
            new string[]
            {
				// ... add any modules that your module loads dynamically here ...
			}
            );
    }
}
