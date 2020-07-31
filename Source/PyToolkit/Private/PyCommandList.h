// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "EditorStyleSet.h"

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

	// OpenLauncher Command
	TSharedPtr<FUICommandInfo> OpenLauncher;
};
