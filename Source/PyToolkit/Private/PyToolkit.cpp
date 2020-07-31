// Copyright Epic Games, Inc. All Rights Reserved.

#include "PyToolkit.h"
#include "PyCommandList.h"

#define LOCTEXT_NAMESPACE "FPyToolkitModule"

void FPyToolkitModule::StartupModule()
{
	// This code will execute after your module is loaded into memory; the exact timing is specified in the .uplugin file per-module

	// Initialize the tick handler
	TickHandle = FTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateLambda([this](float DeltaTime)
	{
		Tick(DeltaTime);
		return true;
	}));
	
	FPyCommandList::Register();
	
}

void FPyToolkitModule::ShutdownModule()
{
	// This function may be called during shutdown to clean up your module.  For modules that support dynamic reloading,
	// we call this function before unloading the module.

}

void FPyToolkitModule::Tick(const float InDeltaTime) {
	// NOTE Reference Python Official Plugin | Trigger initialize.py by tick
	if (!bHasTicked) {
		bHasTicked = true;
		FString InitScript = TEXT("py \"") + FPaths::ProjectPluginsDir() / TEXT("PyToolkit/Content/initialize.py") + TEXT("\"");
		GEngine->Exec(NULL, InitScript.GetCharArray().GetData());
		
		// NOTE Register Launcher Key Event
		FLevelEditorModule& LevelEditorModule = FModuleManager::LoadModuleChecked<FLevelEditorModule>("LevelEditor");
		TSharedPtr< ILevelEditor > LevelEditor = LevelEditorModule.GetFirstLevelEditor();

		TSharedRef<FUICommandList> CommandList = LevelEditorModule.GetGlobalLevelEditorActions();
		//TSharedRef<FUICommandList> CommandList = MakeShareable(new FUICommandList);
		CommandList->MapAction(FPyCommandList::Get().OpenLauncher,
			FExecuteAction::CreateLambda([this]
			{
				FString LauncherScript = TEXT("py \"") + FPaths::ProjectPluginsDir() / TEXT("PyToolkit/Content/UE_Launcher/launcher.py") + TEXT("\"");
				GEngine->Exec(NULL, LauncherScript.GetCharArray().GetData());
			})
			//FExecuteAction::CreateStatic(&FLevelEditorActionCallbacks::ExecuteExecCommand, FString(TEXT("CAMERA ALIGN")))
		);
		LevelEditor->AppendCommands(CommandList);
	}
}

#undef LOCTEXT_NAMESPACE

IMPLEMENT_MODULE(FPyToolkitModule, PyToolkit)