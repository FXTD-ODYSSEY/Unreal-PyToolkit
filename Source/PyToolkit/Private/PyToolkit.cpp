// Copyright Epic Games, Inc. All Rights Reserved.

#include "PyToolkit.h"
#include "PyCommandList.h"

#include "Editor/UnrealEd/Public/Editor.h" 
#include "LevelEditor.h"

#define LOCTEXT_NAMESPACE "FPyToolkitModule"

void FPyToolkitModule::StartupModule()
{
	// This code will execute after your module is loaded into memory; the exact timing is specified in the .uplugin file per-module

	FLevelEditorModule &LevelEditorModule = FModuleManager::LoadModuleChecked<FLevelEditorModule>("LevelEditor");
	TSharedPtr<FExtensibilityManager> Manager = LevelEditorModule.GetMenuExtensibilityManager();
	TSharedPtr<FExtender> MenuExtender = MakeShareable(new FExtender);

	struct Local
	{
		static void ExtendMenu(FMenuBuilder& MenuBuilder)
		{
			FUIAction Action(
				FExecuteAction::CreateLambda([] {
				FString LauncherScript = TEXT("py \"") + FPaths::ProjectPluginsDir() / TEXT("PyToolkit/Content/UE_Launcher/launcher.py") + TEXT("\"");
				GEngine->Exec(NULL, LauncherScript.GetCharArray().GetData());
			}));

			MenuBuilder.AddMenuEntry(
				LOCTEXT("TestTools", "Test Tools"),
				LOCTEXT("TestToolsTooltip", "Test List of tools"),
				FSlateIcon(),
				Action);3

			// // one extra entry when summoning the menu this way
			// MenuBuilder.BeginSection("ActorPreview", LOCTEXT("PreviewHeading", "Preview"));
			// {
			// 	// Note: not using a command for play from here since it requires a mouse click
			// 	FUIAction PlayFromHereAction(
			// 		FExecuteAction::CreateLambda([] {
			// 		FString LauncherScript = TEXT("py \"") + FPaths::ProjectPluginsDir() / TEXT("PyToolkit/Content/UE_Launcher/launcher.py") + TEXT("\"");
			// 		GEngine->Exec(NULL, LauncherScript.GetCharArray().GetData());
			// 	}));

			// 	const FText PlayFromHereLabel = GEditor->OnlyLoadEditorVisibleLevelsInPIE() ? LOCTEXT("PlayFromHereVisible", "Play From Here (visible levels)") : LOCTEXT("PlayFromHere", "Play From Here");
			// 	MenuBuilder.AddMenuEntry(PlayFromHereLabel, LOCTEXT("PlayFromHere_ToolTip", "Starts a game preview from the clicked location"), FSlateIcon(), PlayFromHereAction);
			// }
			// MenuBuilder.EndSection();
		}
	};

	MenuExtender->AddMenuExtension(
		TEXT("EditMain"),
		EExtensionHook::After,
		TSharedPtr<FUICommandList>(),
		FMenuExtensionDelegate::CreateStatic(&Local::ExtendMenu)
		/*FMenuExtensionDelegate::CreateLambda([this] {
			UE_LOG(LogTemp, Error, TEXT("Menu PyToolkitTest"));
		})*/
	);
	Manager->AddExtender(MenuExtender);

	
	// Initialize the tick handler
	TickHandle = FTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateLambda([this](float DeltaTime) {
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

void FPyToolkitModule::Tick(const float InDeltaTime)
{
	// NOTE Reference Python Official Plugin | Trigger initialize.py by tick
	if (!bHasTicked)
	{
		bHasTicked = true;
		FString InitScript = TEXT("py \"") + FPaths::ProjectPluginsDir() / TEXT("PyToolkit/Content/initialize.py") + TEXT("\"");
		GEngine->Exec(NULL, InitScript.GetCharArray().GetData());

		// NOTE Register Launcher Key Event
		FLevelEditorModule &LevelEditorModule = FModuleManager::LoadModuleChecked<FLevelEditorModule>("LevelEditor");
		TSharedPtr<ILevelEditor> LevelEditor = LevelEditorModule.GetFirstLevelEditor();

		TSharedRef<FUICommandList> CommandList = LevelEditorModule.GetGlobalLevelEditorActions();
		//TSharedRef<FUICommandList> CommandList = MakeShareable(new FUICommandList);
		CommandList->MapAction(FPyCommandList::Get().OpenLauncher,
							   FExecuteAction::CreateLambda([this] {
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