// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "Kismet/BlueprintFunctionLibrary.h"

#include "Runtime/AssetRegistry/Public/AssetRegistryModule.h"
#include "UnrealEd/Public/Subsystems/AssetEditorSubsystem.h"
#include "UnrealEd/Public/Toolkits/AssetEditorManager.h"
#include "Runtime/LevelSequence/Public/LevelSequence.h"
//#include "SequencerScripting/Private/SequencerBindingProxy.h"
#include "Editor/Sequencer/Public/ISequencer.h"
#include "Editor/Sequencer/Public/IKeyArea.h"

#include "LevelSequenceEditor/Private/LevelSequenceEditorToolkit.h"
#include "MovieSceneTrack.h"
#include "Kismet/KismetRenderingLibrary.h"
#include "ObjectTools.h"

#include "Runtime/Engine/Classes/Engine/TextureRenderTargetCube.h"
#include "Runtime/Engine/Classes/Engine/TextureCube.h"
#include "Developer/AssetTools/Public/AssetToolsModule.h"
#include "UnrealEd/Public/PackageTools.h"

#include "Engine/SkeletalMeshSocket.h"
#include "Runtime/Engine/Classes/Animation/Skeleton.h"
#include "Editor/SkeletonEditor/Private/SkeletonTreeManager.h"
#include "Editor/SkeletonEditor/Public/ISkeletonTree.h"
#include "Editor/SkeletonEditor/Public/IEditableSkeleton.h"
#include "Editor/SkeletonEditor/Public/ISkeletonEditorModule.h"

#include "Runtime/Core/Public/Misc/ConfigCacheIni.h"
//PublicDependencyModuleNames-> "UnrealEd"
#include "Editor/UnrealEd/Public/Editor.h"
#include "Editor/UnrealEd/Public/Toolkits/AssetEditorManager.h"
#include "Editor/UnrealEd/Public/LevelEditorViewport.h"
// PublicDependencyModuleNames -> "ContentBrowser"
#include "Editor/ContentBrowser/Public/ContentBrowserModule.h"
#include "Editor/ContentBrowser/Private/SContentBrowser.h"
// PublicDependencyModuleNames -> "AssetRegistry"
#include "Runtime/AssetRegistry/Public/AssetRegistryModule.h"
// PublicDependencyModuleNames -> "PythonScriptPlugin" && "Python"

// Material
#include "Materials/Material.h"
#include "Materials/MaterialInstance.h"
#include "MaterialEditor/MaterialEditorInstanceConstant.h"

#include "Framework/Commands/GenericCommands.h"

#include "PyToolkitBPLibrary.generated.h"

/*
*	Function library class.
*	Each function in it is expected to be static and represents blueprint node that can be called in any blueprint.
*
*	When declaring function you can define metadata for the node. Key function specifiers will be BlueprintPure and BlueprintCallable.
*	BlueprintPure - means the function does not affect the owning object in any way and thus creates a node without Exec pins.
*	BlueprintCallable - makes a function which can be executed in Blueprints - Thus it has Exec pins.
*	DisplayName - full name of the node, shown when you mouse over the node and in the blueprint drop down menu.
*				Its lets you name the node using characters not allowed in C++ function names.
*	CompactNodeTitle - the word(s) that appear on the node.
*	Keywords -	the list of keywords that helps you to find node when you search for it using Blueprint drop-down menu.
*				Good example is "Print String" node which you can find also by using keyword "log".
*	Category -	the category your node will be under in the Blueprint drop-down menu.
*
*	For more info on custom blueprint nodes visit documentation:
*	https://wiki.unrealengine.com/Custom_Blueprint_Node_Creation
*/
UCLASS()
class UPyToolkitBPLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_UCLASS_BODY()

	//UFUNCTION(BlueprintCallable, meta = (DisplayName = "Execute Sample function", Keywords = "PyToolkit sample test testing"), Category = "PyToolkitTesting")
	//static float PyToolkitSampleFunction(float Param);

#pragma region UnrealPythonLibrary
	// copy from https://github.com/AlexQuevillon/UnrealPythonLibrary
	UFUNCTION(BlueprintCallable, Category = "PyToolkit|Lib")
	static TArray<UObject *> GetAllObjects();

	UFUNCTION(BlueprintCallable, Category = "PyToolkit|Lib")
	static TArray<FString> GetAllProperties(UClass *Class);

	UFUNCTION(BlueprintCallable, Category = "PyToolkit|Lib")
	static TArray<FString> GetSelectedFolders();

	UFUNCTION(BlueprintCallable, Category = "PyToolkit|Lib")
	static void SetSelectedAssets(TArray<FString> Paths);

	UFUNCTION(BlueprintCallable, Category = "PyToolkit|Lib")
	static void SetSelectedFolders(TArray<FString> Paths);

	UFUNCTION(BlueprintCallable, Category = "PyToolkit|Lib")
	static void CloseEditorForAssets(TArray<UObject *> Assets);

	UFUNCTION(BlueprintCallable, Category = "PyToolkit|Lib")
	static TArray<UObject *> GetAssetsOpenedInEditor();

	UFUNCTION(BlueprintCallable, Category = "PyToolkit|Lib")
	static void SetFolderColor(FString FolderPath, FLinearColor Color);

	UFUNCTION(BlueprintCallable, Category = "PyToolkit|Lib")
	static void SetViewportLocationAndRotation(int ViewportIndex, FVector Location, FRotator Rotation);

	UFUNCTION(BlueprintCallable, Category = "PyToolkit|Lib")
	static int GetActiveViewportIndex();
#pragma endregion

#pragma region SequencerAPI

	UFUNCTION(BlueprintCallable, Category = "PyToolkit|SequencerAPI")
	static ULevelSequence *GetSequencerSequence();

	UFUNCTION(BlueprintCallable, Category = "PyToolkit|SequencerAPI")
	static TArray<FGuid> GetSequencerSelectedID(ULevelSequence *LevelSeq);

	UFUNCTION(BlueprintCallable, Category = "PyToolkit|SequencerAPI")
	static TArray<UMovieSceneTrack *> GetSequencerSelectedTracks(ULevelSequence *LevelSeq);

	UFUNCTION(BlueprintCallable, Category = "PyToolkit|SequencerAPI")
	static TSet<UMovieSceneSection *> GetSequencerSelectedSections(ULevelSequence *LevelSeq);

	UFUNCTION(BlueprintCallable, Category = "PyToolkit|SequencerAPI")
	static TMap<UMovieSceneSection *, FString> GetSequencerSelectedChannels(ULevelSequence *LevelSeq);

#pragma endregion

#pragma region SocketAPI
	UFUNCTION(BlueprintCallable, Category = "PyToolkit|Socket")
	static USkeletalMeshSocket *AddSkeletalMeshSocket(USkeleton *InSkeleton, FName InBoneName);

	UFUNCTION(BlueprintCallable, Category = "PyToolkit|Socket")
	static void DeleteSkeletalMeshSocket(USkeleton *InSkeleton, TArray<USkeletalMeshSocket *> SocketList);

	UFUNCTION(BlueprintCallable, Category = "PyToolkit|Socket")
	static int32 GetSkeletonBoneNum(USkeleton *InSkeleton);

	UFUNCTION(BlueprintCallable, Category = "PyToolkit|Socket")
	static FName GetSkeletonBoneName(USkeleton *InSkeleton, int32 BoneIndex);
#pragma endregion

#pragma region Material>

	UFUNCTION(BlueprintCallable, Category = "RedArtToolkit|Material")
	static UMaterialInstanceConstant *GetMaterialEditorSourceInstance(UMaterialEditorInstanceConstant *Editor);

	UFUNCTION(BlueprintCallable, Category = "RedArtToolkit|Material")
	static void SetMaterialInstanceStaticSwitchParameterValue(UMaterialInstance *Instance, FName ParameterName, bool Value);
	UFUNCTION(BlueprintCallable, Category = "RedArtToolkit|Material")
	static TArray<UMaterialExpression *> GetMaterialExpressions(UMaterial *Material);

	UFUNCTION(BlueprintCallable, Category = "RedArtToolkit|Material")
	static TArray<UMaterialExpression *> GetMaterialFunctionExpressions(UMaterialFunction *Function);

#pragma endregion

#pragma region Msic

	UFUNCTION(BlueprintCallable, Category = "PyToolkit|Msic")
	static bool ExecLevelEditorAction(FString Action);

	UFUNCTION(BlueprintCallable, Category = "PyToolkit|Msic")
	static UActorComponent *AddComponent(AActor *a, USceneComponent *future_parent, FName name, UClass *NewComponentClass);

	UFUNCTION(BlueprintCallable, Category = "PyToolkit")
	static UTextureCube *RenderTargetCubeCreateStaticTextureCube(UTextureRenderTargetCube *RenderTarget, FString InName);

	UFUNCTION(BlueprintCallable, Category = "PyToolkit|Msic")
	static FString GetCurrentContentPath();

	UFUNCTION(BlueprintCallable, Category = "PyToolkit|Msic")
	static TArray<uint8> GetThumbnail(UObject *MeshObject, int32 _imageRes = 128);
	
	UFUNCTION(BlueprintCallable, Category = "PyToolkit|Msic")
	static void RunFunction(UObject* CDO, UFunction* Function);

#pragma endregion
};
