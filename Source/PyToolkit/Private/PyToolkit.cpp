// Copyright Epic Games, Inc. All Rights Reserved.

#include "PyToolkit.h"
#include "PyCommandList.h"

#include "Editor/UnrealEd/Public/Editor.h"
#include "LevelEditor.h"
#include "ISequencerModule.h"

#define LOCTEXT_NAMESPACE "FPyToolkitModule"

void FPyToolkitModule::StartupModule()
{
	// This code will execute after your module is loaded into memory; the exact timing is specified in the .uplugin file per-module

	// NOTE ∂¡»° json ≈‰÷√
	PluginName = "PyToolkit";
	Content = FPaths::ProjectPluginsDir() / PluginName + TEXT("/Content");

	FString JsonSetting = Content + TEXT("/setting.json");
	TSharedPtr<FJsonObject> JsonObject = FPyCommandList::ReadJson(JsonSetting);
	SettingObject = JsonObject->GetObjectField("script");

	static FFormatNamedArguments Arguments;
	Arguments.Add(TEXT("Content"), FText::FromString(Content));
	FString Script = FText::Format(FTextFormat::FromString(SettingObject->GetStringField("launcher")), Arguments).ToString();
	FPyCommandList::ExtendSequencerMenuEntry(Script);

	FPyCommandList::Register();

	// Initialize the tick handler
	TickHandle = FTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateLambda([this](float DeltaTime) {
		Tick(DeltaTime);
		return true;
	}));
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

		static FFormatNamedArguments Arguments;
		Arguments.Add(TEXT("Content"), FText::FromString(Content));
		FText InitScript = FText::Format(FTextFormat::FromString(SettingObject->GetStringField("initialize")), Arguments);
		GEngine->Exec(NULL, InitScript.ToString().GetCharArray().GetData());

		// NOTE Register Launcher Key Event
		FLevelEditorModule &LevelEditorModule = FModuleManager::LoadModuleChecked<FLevelEditorModule>("LevelEditor");
		TSharedPtr<ILevelEditor> LevelEditor = LevelEditorModule.GetFirstLevelEditor();

		TSharedRef<FUICommandList> CommandList = LevelEditorModule.GetGlobalLevelEditorActions();
		//TSharedRef<FUICommandList> CommandList = MakeShareable(new FUICommandList);

		static FString Launcher = SettingObject->GetStringField("launcher");
		struct Callback
		{
			static void RunCommand()
			{
				FString LauncherScript = FText::Format(FTextFormat::FromString(Launcher), Arguments).ToString();
				GEngine->Exec(NULL, LauncherScript.GetCharArray().GetData());
			}
		};

		CommandList->MapAction(
			FPyCommandList::Get().OpenLauncher,
			FExecuteAction::CreateStatic(&Callback::RunCommand)
		);
		LevelEditor->AppendCommands(CommandList);
	}
}

#undef LOCTEXT_NAMESPACE

IMPLEMENT_MODULE(FPyToolkitModule, PyToolkit)