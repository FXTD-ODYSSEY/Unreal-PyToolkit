// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "Modules/ModuleManager.h"

class FPyToolkitModule : public IModuleInterface
{
public:

	/** IModuleInterface implementation */
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;

private:

	FString PluginName;
	FString Content;
	TSharedPtr<FJsonObject> SettingObject;

	void Tick(const float InDeltaTime);
	bool bHasTicked = false;
	FDelegateHandle TickHandle;

};
