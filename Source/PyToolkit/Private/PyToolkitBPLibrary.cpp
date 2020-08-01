// Copyright Epic Games, Inc. All Rights Reserved.

#include "PyToolkitBPLibrary.h"
#include "PyToolkit.h"

UPyToolkitBPLibrary::UPyToolkitBPLibrary(const FObjectInitializer &ObjectInitializer)
    : Super(ObjectInitializer)
{
}

#pragma region UnrealPythonLibrary
// copy from https://github.com/AlexQuevillon/UnrealPythonLibrary

TArray<FString> UPyToolkitBPLibrary::GetAllProperties(UClass *Class)
{
    TArray<FString> Ret;
    if (Class != nullptr)
    {
        for (TFieldIterator<UProperty> It(Class); It; ++It)
        {
            UProperty *Property = *It;
            if (Property->HasAnyPropertyFlags(EPropertyFlags::CPF_Edit))
            {
                Ret.Add(Property->GetName());
            }
        }
    }
    return Ret;
}

TArray<FString> UPyToolkitBPLibrary::GetSelectedAssets()
{
    FContentBrowserModule &ContentBrowserModule = FModuleManager::LoadModuleChecked<FContentBrowserModule>("ContentBrowser");
    TArray<FAssetData> SelectedAssets;
    ContentBrowserModule.Get().GetSelectedAssets(SelectedAssets);
    TArray<FString> Result;
    for (FAssetData &AssetData : SelectedAssets)
    {
        Result.Add(AssetData.PackageName.ToString());
    }
    return Result;
}

void UPyToolkitBPLibrary::SetSelectedAssets(TArray<FString> Paths)
{
    FContentBrowserModule &ContentBrowserModule = FModuleManager::LoadModuleChecked<FContentBrowserModule>("ContentBrowser");
    FAssetRegistryModule &AssetRegistryModule = FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry");
    TArray<FName> PathsName;
    for (FString Path : Paths)
    {
        PathsName.Add(*Path);
    }
    FARFilter AssetFilter;
    AssetFilter.PackageNames = PathsName;
    TArray<FAssetData> AssetDatas;
    AssetRegistryModule.Get().GetAssets(AssetFilter, AssetDatas);
    ContentBrowserModule.Get().SyncBrowserToAssets(AssetDatas);
}

TArray<FString> UPyToolkitBPLibrary::GetSelectedFolders()
{
    FContentBrowserModule &ContentBrowserModule = FModuleManager::LoadModuleChecked<FContentBrowserModule>("ContentBrowser");
    TArray<FString> SelectedFolders;
    ContentBrowserModule.Get().GetSelectedFolders(SelectedFolders);
    return SelectedFolders;
}

void UPyToolkitBPLibrary::SetSelectedFolders(TArray<FString> Paths)
{
    FContentBrowserModule &ContentBrowserModule = FModuleManager::LoadModuleChecked<FContentBrowserModule>("ContentBrowser");
    ContentBrowserModule.Get().SyncBrowserToFolders(Paths);
}

void UPyToolkitBPLibrary::CloseEditorForAssets(TArray<UObject *> Assets)
{
    FAssetEditorManager &AssetEditorManager = FAssetEditorManager::Get();
    for (UObject *Asset : Assets)
    {
        AssetEditorManager.CloseAllEditorsForAsset(Asset);
    }
}

TArray<UObject *> UPyToolkitBPLibrary::GetAssetsOpenedInEditor()
{
    FAssetEditorManager &AssetEditorManager = FAssetEditorManager::Get();
    return AssetEditorManager.GetAllEditedAssets();
}

void UPyToolkitBPLibrary::SetFolderColor(FString FolderPath, FLinearColor Color)
{
    GConfig->SetString(TEXT("PathColor"), *FolderPath, *Color.ToString(), GEditorPerProjectIni);
}

int UPyToolkitBPLibrary::GetActiveViewportIndex()
{
    int Index = 1;
    if (GEditor != nullptr && GCurrentLevelEditingViewportClient != nullptr)
    {
        GEditor->GetLevelViewportClients().Find(GCurrentLevelEditingViewportClient, Index);
    }
    return Index;
}

// ViewportIndex is affected by the spawning order and not the viewport number.
//    e.g. Viewport 4 can be the first one if the user spawned it first.
//         And can become the last one if the user open the other ones and then close and re-open Viewport 4.
//    Also, the indexes are confusing.
// 1st Spawned Viewport : Index = 1
// 2nd Spawned Viewport : Index = 5
// 3rd Spawned Viewport : Index = 9
// 4th Spawned Viewport : Index = 13
void UPyToolkitBPLibrary::SetViewportLocationAndRotation(int ViewportIndex, FVector Location, FRotator Rotation)
{
    if (GEditor != nullptr && ViewportIndex < GEditor->GetLevelViewportClients().Num())
    {
        FLevelEditorViewportClient *LevelViewportClient = GEditor->GetLevelViewportClients()[ViewportIndex];
        if (LevelViewportClient != nullptr)
        {
            LevelViewportClient->SetViewLocation(Location);
            LevelViewportClient->SetViewRotation(Rotation);
        }
    }
}

#pragma endregion

#pragma region SequencerAPI

ULevelSequence *UPyToolkitBPLibrary::GetFocusSequence()
{
    UAssetEditorSubsystem *sub = GEditor->GetEditorSubsystem<UAssetEditorSubsystem>();
    TArray<UObject *> assets = sub->GetAllEditedAssets();

    for (UObject *asset : assets)
    {
        // Get LevelSequenceEditor

        IAssetEditorInstance *AssetEditor = sub->FindEditorForAsset(asset, false);
        FLevelSequenceEditorToolkit *LevelSequenceEditor = (FLevelSequenceEditorToolkit *)AssetEditor;

        if (LevelSequenceEditor != nullptr)
        {
            ULevelSequence *LevelSeq = Cast<ULevelSequence>(asset);
            return LevelSeq;
        }
    }

    return nullptr;
}

TArray<FGuid> UPyToolkitBPLibrary::GetFocusBindings(ULevelSequence *LevelSeq)
{
    IAssetEditorInstance *AssetEditor = GEditor->GetEditorSubsystem<UAssetEditorSubsystem>()->FindEditorForAsset(LevelSeq, false);

    FLevelSequenceEditorToolkit *LevelSequenceEditor = (FLevelSequenceEditorToolkit *)AssetEditor;

    TArray<FGuid> SelectedGuid;
    if (LevelSequenceEditor != nullptr)
    {
        // Get current Sequencer
        ISequencer *Sequencer = LevelSequenceEditor->GetSequencer().Get();

        Sequencer->GetSelectedObjects(SelectedGuid);
        return SelectedGuid;
    }

    return SelectedGuid;
}

// void UPyToolkitBPLibrary::ExtendSequencerBindingMenu()
// {
//     IAssetEditorInstance *AssetEditor = GEditor->GetEditorSubsystem<UAssetEditorSubsystem>()->FindEditorForAsset(LevelSeq, false);

//     FLevelSequenceEditorToolkit *LevelSequenceEditor = (FLevelSequenceEditorToolkit *)AssetEditor;

//     TArray<FGuid> SelectedGuid;
//     if (!LevelSequenceEditor)
//         return nullptr;

//     // Get current Sequencer
//     ISequencer *Sequencer = LevelSequenceEditor->GetSequencer().Get();

//     TSharedPtr<FExtensibilityManager> Manager = Sequencer->GetObjectBindingContextMenuExtensibilityManager();
//     TSharedPtr<FExtender> MenuExtender = MakeShareable(new FExtender);

//     Extender->AddMenuExtension(
//         "PyToolkitTest",
//         EExtensionHook::After,
//         TSharedPtr< FUICommandList >(),
//         FMenuExtensionDelegate::CreateLambda([this] {
//             UE_Log(LogTemp, Error, TEXT("PyToolkitTest"));
//         }));

//     manager.AddExtender(MenuExtender)
// }

#pragma endregion

#pragma region SocketAPI

USkeletalMeshSocket *UPyToolkitBPLibrary::AddSkeletalMeshSocket(USkeleton *InSkeleton, FName InBoneName)
{
    USkeletalMeshSocket *socket = nullptr;

    ISkeletonEditorModule &SkeletonEditorModule = FModuleManager::LoadModuleChecked<ISkeletonEditorModule>("SkeletonEditor");
    TSharedRef<IEditableSkeleton> EditableSkeleton = SkeletonEditorModule.CreateEditableSkeleton(InSkeleton);
    socket = EditableSkeleton->AddSocket(InBoneName);
    return socket;
}

void UPyToolkitBPLibrary::DeleteSkeletalMeshSocket(USkeleton *InSkeleton, TArray<USkeletalMeshSocket *> SocketList)
{
    InSkeleton->Modify();
    for (USkeletalMeshSocket *Socket : SocketList)
    {
        InSkeleton->Sockets.Remove(Socket);
    }
    ISkeletonEditorModule &SkeletonEditorModule = FModuleManager::LoadModuleChecked<ISkeletonEditorModule>("SkeletonEditor");
    TSharedRef<IEditableSkeleton> EditableSkeleton = SkeletonEditorModule.CreateEditableSkeleton(InSkeleton);
    EditableSkeleton->RefreshBoneTree();
}

int32 UPyToolkitBPLibrary::GetSkeletonBoneNum(USkeleton *InSkeleton)
{
    return InSkeleton->GetReferenceSkeleton().GetNum();
}

FName UPyToolkitBPLibrary::GetSkeletonBoneName(USkeleton *InSkeleton, int32 BoneIndex)
{
    return InSkeleton->GetReferenceSkeleton().GetBoneName(BoneIndex);
}

#pragma endregion

#pragma region Msic

// https://forums.unrealengine.com/development-discussion/python-scripting/1703959-how-to-add-component-to-existing-actor-in-level-with-python-blueprint
//You pass to it class of component, otherwise it creates StaticMeshComponent
UActorComponent *UPyToolkitBPLibrary::AddComponent(AActor *a, USceneComponent *future_parent, FName name, UClass *NewComponentClass)
{

    UActorComponent *retComponent = nullptr;
    if (NewComponentClass)
    {
        UActorComponent *NewComponent = NewObject<UActorComponent>(a, NewComponentClass, name);
        FTransform CmpTransform; // = dup_source->GetComponentToWorld();
        //NewComponent->AttachToComponent(sc, FAttachmentTransformRules::KeepWorldTransform);
        // Do Scene Attachment if this new Comnponent is a USceneComponent
        if (USceneComponent *NewSceneComponent = Cast<USceneComponent>(NewComponent))
        {
            if (future_parent != 0)
                NewSceneComponent->AttachToComponent(future_parent, FAttachmentTransformRules::KeepWorldTransform);
            else
                NewSceneComponent->AttachToComponent(a->GetRootComponent(), FAttachmentTransformRules::KeepWorldTransform);

            NewSceneComponent->SetComponentToWorld(CmpTransform);
        }
        a->AddInstanceComponent(NewComponent);
        NewComponent->OnComponentCreated();
        NewComponent->RegisterComponent();

        a->RerunConstructionScripts();
        retComponent = NewComponent;
    }

    return retComponent;
}

UTextureCube *UPyToolkitBPLibrary::RenderTargetCubeCreateStaticTextureCube(UTextureRenderTargetCube *RenderTarget, FString InName)
{
    FString Name;
    FString PackageName;
    IAssetTools &AssetTools = FModuleManager::Get().LoadModuleChecked<FAssetToolsModule>("AssetTools").Get();

    //Use asset name only if directories are specified, otherwise full path
    if (!InName.Contains(TEXT("/")))
    {
        FString AssetName = RenderTarget->GetOutermost()->GetName();
        const FString SanitizedBasePackageName = UPackageTools::SanitizePackageName(AssetName);
        const FString PackagePath = FPackageName::GetLongPackagePath(SanitizedBasePackageName) + TEXT("/");
        AssetTools.CreateUniqueAssetName(PackagePath, InName, PackageName, Name);
    }
    else
    {
        InName.RemoveFromStart(TEXT("/"));
        InName.RemoveFromStart(TEXT("Content/"));
        InName.StartsWith(TEXT("Game/")) == true ? InName.InsertAt(0, TEXT("/")) : InName.InsertAt(0, TEXT("/Game/"));
        AssetTools.CreateUniqueAssetName(InName, TEXT(""), PackageName, Name);
    }

    UTextureCube *NewTex = nullptr;

    // create a static 2d texture
    NewTex = RenderTarget->ConstructTextureCube(CreatePackage(NULL, *PackageName), Name, RenderTarget->GetMaskedFlags() | RF_Public | RF_Standalone);
    if (NewTex != nullptr)
    {
        // package needs saving
        NewTex->MarkPackageDirty();

        // Notify the asset registry
        FAssetRegistryModule::AssetCreated(NewTex);
    }
    return NewTex;
}

#pragma endregion
