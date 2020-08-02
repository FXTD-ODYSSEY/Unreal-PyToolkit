// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "EditorStyleSet.h"

#include "Json.h"

#include "LevelEditor.h"
#include "ISequencerModule.h"
#include "Editor/UnrealEd/Public/Editor.h" 

#include "Editor/LevelEditor/Public/LevelEditor.h"
#include "Editor//LevelEditor/Public/ILevelEditor.h"
#include "Editor//LevelEditor/Public/LevelEditorActions.h"

#include "Framework/Commands/Commands.h"

// Actions that can be invoked in the reference viewer
class FPyCommandList : public TCommands<FPyCommandList>
{
public:
	FPyCommandList();

	// TCommands<> interface
	virtual void RegisterCommands() override;
	// End of TCommands<> interface
	
	static TSharedPtr<FJsonObject> ReadJson(const FString path);
	static void ExtendSequencerMenuEntry(FString LauncherScript);

	// OpenLauncher Command
	TSharedPtr<FUICommandInfo> OpenLauncher;
};
